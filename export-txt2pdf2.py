import os
import re
import json
import hashlib
import datetime
from typing import List, Tuple, Dict

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
)
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from xml.sax.saxutils import escape as xml_escape  # 转义 <>&


# ========== 配置 ==========
TXT_ROOT = "/Users/myu/chat-his"                    # 你的 txt 根目录
PDF_PREFIX = "chat_ebook"              # PDF 前缀
STATE_FILE = "ebook_state.json"        # 记录每个 txt 的 md5
# ==========================


def register_chinese_font():
    """注册中文字体，避免中文变方块。"""
    try:
        font_path = "/System/Library/Fonts/STHeiti Medium.ttc"
        pdfmetrics.registerFont(TTFont("CH_FONT", font_path))
        return "CH_FONT"
    except Exception:
        return "Helvetica"


def hash_file(path: str) -> str:
    """计算文件 md5，用于判断内容是否有变化。"""
    m = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            m.update(chunk)
    return m.hexdigest()


def find_all_txt_files(root: str) -> List[str]:
    """找到 root 下所有 txt 文件，返回相对路径列表。"""
    txt_files: List[str] = []
    for dp, dn, fn in os.walk(root):
        for name in fn:
            if name.lower().endswith(".txt"):
                full = os.path.join(dp, name)
                rel = os.path.relpath(full, root)
                txt_files.append(rel)
    return sorted(txt_files)


def extract_questions_from_txt(content: str) -> List[str]:
    """
    从 txt 中抽取“问题索引（User Questions）”里的问题：
    ============ 问题索引（User Questions） ============
    1. 问题1
    2. 问题2
    ...
    ====================================================
    """
    lines = content.splitlines()
    in_index = False
    questions: List[str] = []

    for line in lines:
        if line.startswith("============ 问题索引"):
            in_index = True
            continue
        if in_index and line.startswith("==="):
            break
        if in_index:
            m = re.match(r"\s*(\d+)\.\s*(.+)", line)
            if m:
                q = m.group(2).strip()
                if q:
                    questions.append(q)

    return questions


def load_state() -> Dict[str, str]:
    """读取上次记录的 txt 状态（相对路径 -> md5）。"""
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


def save_state(state: Dict[str, str]):
    """保存当前 txt 状态到 STATE_FILE。"""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def normalize_content(raw: str) -> str:
    """
    轻量、安全的结构修正：
    - 统一真实换行
    - 把字面量 '\\n' / '\\r' 换成真正换行
    - 把 '\\t' 和真实制表符统一成空格
    """
    s = raw.replace("\r\n", "\n").replace("\r", "\n")
    s = s.replace("\\r\\n", "\n")
    s = s.replace("\\n", "\n")
    s = s.replace("\\r", "\n")
    s = s.replace("\\t", "    ")
    s = s.replace("\t", "    ")
    return s


def get_dated_pdf_name(prefix: str) -> str:
    """
    根据当天日期生成一个不重名的 PDF 文件名：
      chat_ebook_20251130.pdf
      chat_ebook_20251130_2.pdf
    """
    today = datetime.date.today().strftime("%Y%m%d")
    base = f"{prefix}_{today}"
    candidates = [f for f in os.listdir(".") if f.startswith(base) and f.endswith(".pdf")]

    if not candidates:
        return f"{base}.pdf"

    max_idx = 1
    for name in candidates:
        s = name[len(base):-4]  # 去掉前缀和 .pdf
        if not s:
            idx = 1
        else:
            m = re.match(r"_(\d+)", s)
            idx = int(m.group(1)) if m else 1
        if idx > max_idx:
            max_idx = idx
    next_idx = max_idx + 1

    # 如果已有 base.pdf，则从 _2 开始
    if any(name == f"{base}.pdf" for name in candidates):
        return f"{base}_{next_idx}.pdf"
    else:
        return f"{base}.pdf"


def collect_questions_and_texts_for_files(
    txt_root: str,
    rel_paths: List[str],
) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    """
    只针对给定的这些 txt 文件，返回：
      - all_questions: [(问题文本, 文件名), ...]
      - file_texts:     [(相对路径, 全文内容), ...]
    """
    all_questions: List[Tuple[str, str]] = []
    file_texts: List[Tuple[str, str]] = []

    for rel in rel_paths:
        full = os.path.join(txt_root, rel)

        # 读文件内容
        try:
            with open(full, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(full, "r", encoding="gbk") as f:
                content = f.read()

        file_texts.append((rel, content))

        qs = extract_questions_from_txt(content)
        base = os.path.basename(rel)
        for q in qs:
            all_questions.append((q, base))

    return all_questions, file_texts


def build_pdf_for_files(
    txt_root: str,
    rel_paths: List[str],
    output_pdf: str,
):
    """
    针对指定的 txt 文件生成一个 PDF：
    - 顶部：这批文件的“问题目录”
    - 后面：每个文件的全文
    """
    if not rel_paths:
        print("没有需要导出的 txt 文件，跳过生成 PDF。")
        return

    font_name = register_chinese_font()

    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="TitleCH",
        fontName=font_name,
        fontSize=20,
        leading=24,
        wordWrap="CJK",
    ))
    styles.add(ParagraphStyle(
        name="HeadingCH",
        fontName=font_name,
        fontSize=14,
        leading=18,
        spaceBefore=6,
        spaceAfter=6,
        wordWrap="CJK",
    ))
    styles.add(ParagraphStyle(
        name="NormalCH",
        fontName=font_name,
        fontSize=10,
        leading=14,
        wordWrap="CJK",
    ))
    styles.add(ParagraphStyle(
        name="TextCH",
        fontName=font_name,
        fontSize=9,
        leading=12,
        wordWrap="CJK",
    ))

    story = []

    all_questions, file_texts = collect_questions_and_texts_for_files(txt_root, rel_paths)

    # ① 问题目录
    story.append(Paragraph("对话问题目录（本次新增/变更）", styles["TitleCH"]))
    story.append(Spacer(1, 12))

    if all_questions:
        for i, (q, base) in enumerate(all_questions, 1):
            para = f"{i}. {xml_escape(q)}（来自：{xml_escape(base)}）"
            story.append(Paragraph(para, styles["NormalCH"]))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("（本次这些 txt 中未找到问题索引）", styles["NormalCH"]))

    story.append(PageBreak())

    # ② 各文件全文
    for rel, raw_content in file_texts:
        base = os.path.basename(rel)

        story.append(Paragraph(f"文件：{xml_escape(base)}", styles["HeadingCH"]))
        story.append(Spacer(1, 6))

        content = normalize_content(raw_content)

        for line in content.splitlines():
            if not line.strip():
                story.append(Spacer(1, 6))
            else:
                safe_line = xml_escape(line)
                story.append(Paragraph(safe_line, styles["TextCH"]))

        story.append(PageBreak())

    doc.build(story)
    print(f"PDF 已生成：{output_pdf}")


def main():
    # 1. 读取上次状态
    old_state = load_state()

    # 2. 计算当前所有 txt 的 md5
    txt_files = find_all_txt_files(TXT_ROOT)
    new_state: Dict[str, str] = {}
    for rel in txt_files:
        full = os.path.join(TXT_ROOT, rel)
        new_state[rel] = hash_file(full)

    # 3. 找出“新增的”文件和“内容发生变化”的文件
    new_paths = [p for p in txt_files if p not in old_state]
    changed_paths = [p for p in txt_files
                     if p in old_state and old_state[p] != new_state[p]]

    files_to_export = sorted(set(new_paths + changed_paths))

    if not files_to_export:
        print("没有新增或变更的 txt 文件，不生成新的 PDF。")
        return

    print("本次将导出这些 txt 文件到新的 PDF：")
    for p in files_to_export:
        print("  -", p)

    # 4. 生成带日期后缀、不重名的 PDF
    pdf_name = get_dated_pdf_name(PDF_PREFIX)

    # 5. 针对这批文件生成 PDF
    build_pdf_for_files(TXT_ROOT, files_to_export, pdf_name)

    # 6. 更新状态文件（下次就不会重复导出它们）
    save_state(new_state)


if __name__ == "__main__":
    main()
