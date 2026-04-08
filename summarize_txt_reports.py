import datetime
import os
import re
import subprocess
import tempfile
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


TXT_DIR = Path("txt")
OUT_DIR = Path("out")
MD_OUTPUT = OUT_DIR / "txt_summary_report.md"
PDF_OUTPUT = OUT_DIR / "txt_summary_report.pdf"
OBSIDIAN_DIR = OUT_DIR / "obsidian"
OBSIDIAN_INDEX = OBSIDIAN_DIR / "00-总索引.md"
OBSIDIAN_CATEGORY_DIR = OBSIDIAN_DIR / "分类汇总"
OBSIDIAN_FILE_DIR = OBSIDIAN_DIR / "逐文件摘要"


NOISE_PATTERNS = [
    r"\[request interrupted.*?\]",
    r"^继续$",
    r"^resume$",
    r"^warmup$",
    r"^caveat:",
    r"^this session is being continued",
    r"^<system-reminder>",
    r"^<command-name>",
    r"^<local-command",
    r"^<bash-",
    r"^/compact$",
    r"^/context$",
    r"^/login$",
    r"^/plugin$",
    r"^\(no content\)$",
    r"^the user is asking about",
]


CATEGORY_RULES = [
    {
        "name": "表单与流程",
        "summary": "围绕表单、流程、公文和审批链路的实现与问题排查。",
        "patterns": [
            (r"表单|cap4|xsn|流程|工作流|bpm|公文|govdoc|审批|节点|workitem|已阅|督办|事项", 3),
        ],
    },
    {
        "name": "接口与集成",
        "summary": "关注 REST/API 调用、第三方对接、参数设计与接口落地方式。",
        "patterns": [
            (r"\bapi\b|\brest\b|接口|postman|调用|对接|集成|回调|请求|响应|token|oauth|redis", 3),
        ],
    },
    {
        "name": "前端与移动端",
        "summary": "聚焦 H5、页面报错、前端展示和移动端兼容问题。",
        "patterns": [
            (r"h5|移动端|前端|页面|portal|theme|浏览器|js\b|css\b|html|ui|页面报错", 3),
        ],
    },
    {
        "name": "登录权限与会话",
        "summary": "聚焦登录、用户识别、权限和被迫下线等会话问题。",
        "patterns": [
            (r"登录|下线|帐号|账号|用户|权限|session|会话|认证|单点|失去连接", 3),
        ],
    },
    {
        "name": "日志与监控",
        "summary": "围绕日志打印、日志归档、性能统计和监控可观测性。",
        "patterns": [
            (r"日志|log|systemout|监控|性能|统计|埋点|观测|trace", 3),
        ],
    },
    {
        "name": "数据库与数据模型",
        "summary": "关注表结构、字段含义、SQL、缓存和数据关系。",
        "patterns": [
            (r"数据库|表中|表\b|字段|sql|建表|索引|查询|数据|缓存|redis", 3),
        ],
    },
    {
        "name": "代码设计与源码分析",
        "summary": "围绕类、方法、模块设计、实现原理和源码阅读。",
        "patterns": [
            (r"原理|设计|思想|核心类|核心实现|实现类|模块|架构|源码|source code|代码|分析|配置|类\b|方法|功能", 2),
        ],
    },
    {
        "name": "运维与自动化",
        "summary": "聚焦脚本、仓库、导出、插件、自动化流程和工程工具。",
        "patterns": [
            (r"git|脚本|plugin|技能|skill|pdf|txt|导出|转换|仓库|提交|自动化|obsidian", 3),
        ],
    },
    {
        "name": "时间与业务规则",
        "summary": "聚焦工作日、截止时间和特殊业务规则配置。",
        "patterns": [
            (r"工作日|非工作日|节假日|deadline|time返回值|2099|3000|年份|日期|时间", 3),
        ],
    },
    {
        "name": "问题排查与修复",
        "summary": "围绕异常、报错、定位原因和修复方案。",
        "patterns": [
            (r"报错|异常|错误|问题|排查|定位|修复|什么情况|如何解决|原因", 2),
        ],
    },
]


@dataclass
class QuestionEntry:
    text: str
    summary: str
    review_tip: str
    category: str
    block_id: str


@dataclass
class FileSummary:
    name: str
    question_count: int
    valid_count: int
    dominant_categories: List[str]
    highlights: List[QuestionEntry]
    questions: List[QuestionEntry]


def normalize_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def slugify(text: str, limit: int = 36) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    cleaned = []
    for ch in normalized:
        if ch.isascii() and (ch.isalnum() or ch in "-_"):
            cleaned.append(ch.lower())
        elif "\u4e00" <= ch <= "\u9fff":
            cleaned.append(ch)
        elif ch in {" ", "/", ":"}:
            cleaned.append("-")
    slug = "".join(cleaned)
    slug = re.sub(r"-+", "-", slug).strip("-_")
    return slug[:limit] or "item"


def parse_question_section(content: str) -> List[str]:
    start = content.find("对话问题目录")
    if start == -1:
        return []
    end_candidates = []
    for marker in ("\n文件：", "\nUSER:", "\n============ 问题索引"):
        idx = content.find(marker, start)
        if idx != -1:
            end_candidates.append(idx)
    end = min(end_candidates) if end_candidates else len(content)
    section = content[start:end]

    questions: List[str] = []
    current = ""
    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("对话问题目录"):
            continue
        matched = re.match(r"^(\d+)\.\s*(.*)$", line)
        if matched:
            if current:
                questions.append(current.strip())
            current = matched.group(2).strip()
        elif current and not set(line) <= {"=", "-"}:
            current += " " + line
    if current:
        questions.append(current.strip())

    cleaned = []
    for item in questions:
        item = re.sub(r"（来自：.*?）", "", item)
        item = normalize_text(item)
        if item:
            cleaned.append(item)
    return cleaned


def is_noise(question: str) -> bool:
    q = question.strip().lower()
    if len(q) <= 1:
        return True
    return any(re.search(pattern, q, re.I) for pattern in NOISE_PATTERNS)


def score_categories(question: str) -> Dict[str, int]:
    scores: Dict[str, int] = {}
    for rule in CATEGORY_RULES:
        total = 0
        for pattern, weight in rule["patterns"]:
            matches = re.findall(pattern, question, re.I)
            if matches:
                total += len(matches) * weight
        if total:
            scores[rule["name"]] = total
    return scores


def top_categories_for_scores(scores_list: Sequence[Dict[str, int]]) -> List[str]:
    total = Counter()
    for scores in scores_list:
        total.update(scores)
    if not total:
        return ["其他"]
    return [name for name, _ in total.most_common(3)]


def summarize_question(question: str, category: str) -> Tuple[str, str]:
    q = normalize_text(question)
    if len(q) > 84:
        short = q[:84].rstrip("，。；;,. ") + "..."
    else:
        short = q

    intent_map = [
        (r"原理|设计|思想|架构", "重点在理解设计原理、模块边界和整体实现思路。"),
        (r"核心类|实现类|方法|源码|代码", "重点在定位核心类与关键方法，并梳理调用链。"),
        (r"报错|异常|错误|什么情况|原因", "重点在定位触发条件、根因和排查路径。"),
        (r"如何解决|方案|优化|修复|修改", "重点在比较可行方案、改动范围和落地步骤。"),
        (r"接口|rest|api|postman|调用", "重点在梳理接口入参、调用方式、返回结构和对应实现。"),
        (r"表|字段|sql|数据库|redis", "重点在弄清数据模型、字段含义和数据流转关系。"),
        (r"登录|session|下线|权限|认证", "重点在梳理会话机制、身份识别和失效场景。"),
        (r"前端|页面|h5|移动端|theme|portal", "重点在确认前端表现、兼容性问题和请求链路。"),
        (r"日志|监控|性能|统计", "重点在统一日志口径、补足监控指标和定位性能瓶颈。"),
        (r"工作日|截止时间|年份|日期|时间", "重点在明确业务规则、边界日期和配置入口。"),
        (r"git|脚本|导出|转换|obsidian|pdf|txt", "重点在自动化流程、文件组织方式和后续复用。"),
    ]

    tip = f"这条问题归入“{category}”，复习时优先关注对应实现入口和约束条件。"
    for pattern, candidate in intent_map:
        if re.search(pattern, q, re.I):
            tip = candidate
            break

    prefix = f"这条问题主要在处理“{category}”方向："
    if re.search(r"如何|怎么|给出方案|方案", q):
        summary = prefix + "核心目标是拿到可执行方案，而不是只看概念说明。"
    elif re.search(r"原理|设计|思想|为什么", q):
        summary = prefix + "核心目标是搞清楚设计原因、调用链和关键模块关系。"
    elif re.search(r"报错|异常|错误|原因", q):
        summary = prefix + "核心目标是定位故障根因、触发条件和排查步骤。"
    elif re.search(r"代码|源码|方法|类", q):
        summary = prefix + "核心目标是找到关键代码位置，并提炼真正有用的逻辑。"
    else:
        summary = prefix + "核心目标是把问题从原始提问整理成可复习的知识点。"

    if short:
        summary += f" 原问题聚焦：{short}"
    return summary, tip


def choose_highlights(entries: Sequence[QuestionEntry], limit: int = 3) -> List[QuestionEntry]:
    seen = set()
    highlights: List[QuestionEntry] = []
    for entry in sorted(entries, key=lambda item: (-len(item.text), item.text)):
        key = entry.text[:90]
        if key in seen:
            continue
        highlights.append(entry)
        seen.add(key)
        if len(highlights) >= limit:
            break
    return highlights


def build_file_entries(path: Path, questions: Sequence[str]) -> List[QuestionEntry]:
    entries: List[QuestionEntry] = []
    seen_ids = set()
    for index, question in enumerate(questions, start=1):
        scores = score_categories(question)
        category = max(scores.items(), key=lambda item: (item[1], item[0]))[0] if scores else "其他"
        summary, review_tip = summarize_question(question, category)
        block_id = f"{slugify(path.stem, 18)}-{index}-{slugify(question, 20)}"
        while block_id in seen_ids:
            block_id += "x"
        seen_ids.add(block_id)
        entries.append(
            QuestionEntry(
                text=question,
                summary=summary,
                review_tip=review_tip,
                category=category,
                block_id=block_id,
            )
        )
    return entries


def extract_report_data(txt_dir: Path) -> Tuple[List[FileSummary], Dict[str, dict], int]:
    category_data: Dict[str, dict] = {
        rule["name"]: {
            "summary": rule["summary"],
            "entries": [],
            "files": set(),
        }
        for rule in CATEGORY_RULES
    }
    category_data["其他"] = {
        "summary": "未明显命中预设主题，但仍保留为备查问题。",
        "entries": [],
        "files": set(),
    }

    file_summaries: List[FileSummary] = []
    total_questions = 0

    for path in sorted(txt_dir.glob("*.txt")):
        content = path.read_text(encoding="utf-8", errors="ignore")
        questions = parse_question_section(content)
        total_questions += len(questions)
        valid_questions = [q for q in questions if not is_noise(q)]
        entries = build_file_entries(path, valid_questions)

        per_question_scores = [score_categories(entry.text) for entry in entries]
        for entry in entries:
            category_data[entry.category]["entries"].append((path.name, entry))
            category_data[entry.category]["files"].add(path.name)

        file_summaries.append(
            FileSummary(
                name=path.name,
                question_count=len(questions),
                valid_count=len(entries),
                dominant_categories=top_categories_for_scores(per_question_scores),
                highlights=choose_highlights(entries),
                questions=entries,
            )
        )

    return file_summaries, category_data, total_questions


def build_overview_text(
    file_summaries: Sequence[FileSummary],
    category_data: Dict[str, dict],
    total_questions: int,
) -> List[str]:
    file_count = len(file_summaries)
    valid_count = sum(item.valid_count for item in file_summaries)
    categories_by_count = sorted(
        (
            (name, len(data["entries"]), len(data["files"]))
            for name, data in category_data.items()
            if data["entries"]
        ),
        key=lambda item: (-item[1], item[0]),
    )
    overview = [
        f"- TXT 文件数：{file_count}",
        f"- 提取问题数：{total_questions}",
        f"- 清洗后有效问题数：{valid_count}",
    ]
    if categories_by_count:
        top_names = "、".join(name for name, _, _ in categories_by_count[:5])
        overview.append(f"- 主要关注主题：{top_names}")
    overview.append("- Obsidian 跳转方式：使用标题链接和块链接，不依赖不稳定的行号。")
    return overview


def build_markdown(file_summaries: Sequence[FileSummary], category_data: Dict[str, dict], total_questions: int) -> str:
    generated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: List[str] = []
    lines.append("# TXT 文件总结与分类汇总")
    lines.append("")
    lines.append(f"生成时间：{generated}")
    lines.append("")
    lines.append("## 一、总体概览")
    lines.append("")
    lines.extend(build_overview_text(file_summaries, category_data, total_questions))
    lines.append("")

    lines.append("## 二、分类总览")
    lines.append("")
    lines.append("| 分类 | 问题数 | 涉及文件数 | 说明 |")
    lines.append("| --- | ---: | ---: | --- |")
    categories_by_count = sorted(
        (
            (name, len(data["entries"]), len(data["files"]), data["summary"])
            for name, data in category_data.items()
            if data["entries"]
        ),
        key=lambda item: (-item[1], item[0]),
    )
    for name, q_count, file_count, summary in categories_by_count:
        lines.append(f"| {name} | {q_count} | {file_count} | {summary} |")
    lines.append("")

    lines.append("## 三、重点分类摘要")
    lines.append("")
    for name, q_count, file_count, summary in categories_by_count[:8]:
        data = category_data[name]
        highlights = choose_highlights([entry for _, entry in data["entries"]], limit=4)
        lines.append(f"### {name}")
        lines.append("")
        lines.append(f"- 说明：{summary}")
        lines.append(f"- 规模：{q_count} 个问题，覆盖 {file_count} 个 TXT 文件")
        for idx, entry in enumerate(highlights, start=1):
            lines.append(f"- 代表问题 {idx}：{entry.text}")
            lines.append(f"- 总结要点 {idx}：{entry.summary}")
            lines.append(f"- 复习建议 {idx}：{entry.review_tip}")
        file_list = sorted(data["files"])[:8]
        if file_list:
            lines.append(f"- 关联文件：{', '.join(file_list)}")
        lines.append("")

    lines.append("## 四、按文件摘要")
    lines.append("")
    for item in sorted(file_summaries, key=lambda x: x.name):
        category_text = "、".join(item.dominant_categories)
        lines.append(f"### {item.name}")
        lines.append("")
        lines.append(f"- 问题统计：原始 {item.question_count} 条，清洗后 {item.valid_count} 条")
        lines.append(f"- 主要主题：{category_text}")
        for idx, entry in enumerate(item.highlights, start=1):
            lines.append(f"- 重点问题 {idx}：{entry.text}")
            lines.append(f"- 总结要点 {idx}：{entry.summary}")
        lines.append("")

    lines.append("## 五、Obsidian 使用建议")
    lines.append("")
    lines.append("- 优先打开 `out/obsidian/00-总索引.md`，从分类页或文件页进入。")
    lines.append("- 在 Obsidian 中使用 `[[分类汇总/分类-表单与流程#重点问题]]` 这类标题链接，或 `[[逐文件摘要/chat_ebook_20260127#^块ID]]` 这类块链接。")
    lines.append("- 行号会随着编辑变化，不适合作为长期跳转方式；块 ID 更稳定，也更适合知识库维护。")
    lines.append("")
    return "\n".join(lines)


def write_obsidian_vault(file_summaries: Sequence[FileSummary], category_data: Dict[str, dict]) -> None:
    OBSIDIAN_CATEGORY_DIR.mkdir(parents=True, exist_ok=True)
    OBSIDIAN_FILE_DIR.mkdir(parents=True, exist_ok=True)

    categories_by_count = sorted(
        (
            (name, len(data["entries"]), len(data["files"]), data)
            for name, data in category_data.items()
            if data["entries"]
        ),
        key=lambda item: (-item[1], item[0]),
    )

    index_lines = [
        "# 总索引",
        "",
        "## 分类入口",
        "",
    ]
    for name, count, file_count, _ in categories_by_count:
        note_name = f"分类-{name}"
        index_lines.append(f"- [[分类汇总/{note_name}|{name}]]：{count} 个问题，覆盖 {file_count} 个文件")
    index_lines.extend(["", "## 文件入口", ""])

    for item in sorted(file_summaries, key=lambda x: x.name):
        note_name = Path(item.name).stem
        cats = "、".join(item.dominant_categories)
        index_lines.append(f"- [[逐文件摘要/{note_name}|{item.name}]]：{item.valid_count} 个有效问题，主题 {cats}")

    OBSIDIAN_INDEX.write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    for name, count, file_count, data in categories_by_count:
        note_name = f"分类-{name}"
        lines = [
            f"# {name}",
            "",
            f"- 说明：{data['summary']}",
            f"- 问题数：{count}",
            f"- 涉及文件数：{file_count}",
            "",
            "## 重点问题",
            "",
        ]
        highlights = choose_highlights([entry for _, entry in data["entries"]], limit=8)
        for idx, entry in enumerate(highlights, start=1):
            lines.append(f"### 问题 {idx}")
            lines.append("")
            lines.append(f"- 原问题：{entry.text}")
            lines.append(f"- 总结要点：{entry.summary}")
            lines.append(f"- 复习建议：{entry.review_tip}")
            lines.append("")

        lines.append("## 跳转清单")
        lines.append("")
        for file_name, entry in data["entries"][:80]:
            file_note = Path(file_name).stem
            lines.append(f"- [[逐文件摘要/{file_note}#^{entry.block_id}|{file_name} - {entry.text[:48]}]]")
        (OBSIDIAN_CATEGORY_DIR / f"{note_name}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    for item in file_summaries:
        note_name = Path(item.name).stem
        lines = [
            f"# {item.name}",
            "",
            f"- 原始问题数：{item.question_count}",
            f"- 清洗后问题数：{item.valid_count}",
            f"- 主要主题：{'、'.join(item.dominant_categories)}",
            "",
            "## 重点问题",
            "",
        ]
        for idx, entry in enumerate(item.highlights, start=1):
            lines.append(f"### 重点问题 {idx}")
            lines.append("")
            lines.append(f"- 原问题：{entry.text}")
            lines.append(f"- 总结要点：{entry.summary}")
            lines.append(f"- 复习建议：{entry.review_tip}")
            lines.append("")

        lines.append("## 全部问题卡片")
        lines.append("")
        for idx, entry in enumerate(item.questions, start=1):
            lines.append(f"### 问题 {idx}")
            lines.append(f"^" + entry.block_id)
            lines.append("")
            lines.append(f"- 分类：[[分类汇总/分类-{entry.category}|{entry.category}]]")
            lines.append(f"- 原问题：{entry.text}")
            lines.append(f"- 总结要点：{entry.summary}")
            lines.append(f"- 复习建议：{entry.review_tip}")
            lines.append("")
        (OBSIDIAN_FILE_DIR / f"{note_name}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def markdown_to_pdf(markdown_text: str, output_pdf: Path) -> None:
    swift_code = r"""import Foundation
import AppKit

let args = Array(CommandLine.arguments.dropFirst())
guard args.count == 2 else {
    fputs("usage: swift_md_to_pdf <input.txt> <output.pdf>\n", stderr)
    exit(2)
}

let inputURL = URL(fileURLWithPath: args[0])
let outputURL = URL(fileURLWithPath: args[1])
let text = try String(contentsOf: inputURL, encoding: .utf8)
let nsText = text as NSString

let pageRect = CGRect(x: 0, y: 0, width: 595, height: 842)
let margin: CGFloat = 40
let contentRect = CGRect(x: margin, y: margin, width: pageRect.width - margin * 2, height: pageRect.height - margin * 2)

var mediaBox = pageRect
guard let context = CGContext(outputURL as CFURL, mediaBox: &mediaBox, nil) else {
    fputs("failed to create PDF context\n", stderr)
    exit(1)
}

let style = NSMutableParagraphStyle()
style.lineBreakMode = .byWordWrapping
style.lineSpacing = 2

let attrs: [NSAttributedString.Key: Any] = [
    .font: NSFont.systemFont(ofSize: 11),
    .paragraphStyle: style
]

func fittingLength(from start: Int) -> Int {
    if start >= nsText.length { return 0 }
    var low = 1
    var high = nsText.length - start
    var best = 1
    while low <= high {
        let mid = (low + high) / 2
        let range = NSRange(location: start, length: mid)
        let chunk = nsText.substring(with: range) as NSString
        let rect = chunk.boundingRect(with: contentRect.size, options: [.usesLineFragmentOrigin, .usesFontLeading], attributes: attrs)
        if rect.height <= contentRect.height {
            best = mid
            low = mid + 1
        } else {
            high = mid - 1
        }
    }
    return best
}

func adjustedLength(from start: Int, proposed: Int) -> Int {
    if start + proposed >= nsText.length { return proposed }
    let candidate = nsText.substring(with: NSRange(location: start, length: proposed))
    if let range = candidate.range(of: "\n", options: .backwards) {
        let idx = candidate.distance(from: candidate.startIndex, to: range.lowerBound)
        if idx > proposed / 2 { return idx + 1 }
    }
    if let range = candidate.range(of: " ", options: .backwards) {
        let idx = candidate.distance(from: candidate.startIndex, to: range.lowerBound)
        if idx > proposed / 2 { return idx + 1 }
    }
    return proposed
}

var location = 0
while location < nsText.length {
    let fitted = fittingLength(from: location)
    if fitted <= 0 { break }
    let length = adjustedLength(from: location, proposed: fitted)
    let range = NSRange(location: location, length: length)
    let chunk = nsText.substring(with: range) as NSString

    context.beginPDFPage(nil)
    let graphicsContext = NSGraphicsContext(cgContext: context, flipped: false)
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = graphicsContext
    chunk.draw(with: contentRect, options: [.usesLineFragmentOrigin, .usesFontLeading], attributes: attrs)
    NSGraphicsContext.restoreGraphicsState()
    context.endPDFPage()
    location += length
}

context.closePDF()
"""

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as tmp_text:
        tmp_text.write(markdown_text)
        text_path = Path(tmp_text.name)
    with tempfile.NamedTemporaryFile("w", suffix=".swift", delete=False, encoding="utf-8") as tmp_swift:
        tmp_swift.write(swift_code)
        swift_path = Path(tmp_swift.name)

    env = os.environ.copy()
    env.setdefault("CLANG_MODULE_CACHE_PATH", "/tmp/clang-module-cache")
    try:
        result = subprocess.run(
            ["swift", str(swift_path), str(text_path), str(output_pdf)],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "swift PDF generation failed")
    finally:
        text_path.unlink(missing_ok=True)
        swift_path.unlink(missing_ok=True)


def main() -> int:
    if not TXT_DIR.exists():
        print(f"TXT 目录不存在：{TXT_DIR}")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    file_summaries, category_data, total_questions = extract_report_data(TXT_DIR)
    markdown = build_markdown(file_summaries, category_data, total_questions)
    MD_OUTPUT.write_text(markdown, encoding="utf-8")
    markdown_to_pdf(markdown, PDF_OUTPUT)
    write_obsidian_vault(file_summaries, category_data)

    print(f"Markdown 已生成：{MD_OUTPUT}")
    print(f"PDF 已生成：{PDF_OUTPUT}")
    print(f"Obsidian 索引已生成：{OBSIDIAN_INDEX}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
