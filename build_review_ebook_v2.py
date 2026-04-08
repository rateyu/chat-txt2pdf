import datetime
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from summarize_txt_reports import OUT_DIR, QuestionEntry, choose_highlights, extract_report_data, markdown_to_pdf


MD_OUTPUT = OUT_DIR / "review_ebook_v2.md"
PDF_OUTPUT = OUT_DIR / "review_ebook_v2.pdf"


CHAPTER_PRIORITY = [
    "代码设计与源码分析",
    "问题排查与修复",
    "数据库与数据模型",
    "登录权限与会话",
    "表单与流程",
    "接口与集成",
    "日志与监控",
    "前端与移动端",
    "运维与自动化",
    "时间与业务规则",
    "其他",
]


FOCUS_HINTS = {
    "代码设计与源码分析": "先抓主调用链，再看扩展点和特殊分支。",
    "问题排查与修复": "先记故障现象和触发条件，再记修复动作。",
    "数据库与数据模型": "先看字段职责和数据流，再看 SQL 与缓存。",
    "登录权限与会话": "先确认身份标识，再看 session、cookie、连接状态。",
    "表单与流程": "先看节点状态和表单状态，再判断流程动作。",
    "接口与集成": "先看接口契约，再看参数流转和实现入口。",
    "日志与监控": "先统一日志口径，再补上下文和监控指标。",
    "前端与移动端": "先区分表现层问题和接口问题，再看兼容性。",
    "运维与自动化": "优先把重复动作脚本化，并固定输入输出。",
    "时间与业务规则": "先确认边界年份、默认值和配置入口。",
    "其他": "先把问题重新打标签，再决定是否沉淀为专题。",
}


def sort_categories(category_data: Dict[str, dict]) -> List[Tuple[str, dict]]:
    order = {name: idx for idx, name in enumerate(CHAPTER_PRIORITY)}
    return sorted(
        [(name, data) for name, data in category_data.items() if data["entries"]],
        key=lambda item: (order.get(item[0], 999), -len(item[1]["entries"])),
    )


def top_files(entries: Sequence[Tuple[str, QuestionEntry]], limit: int = 5) -> List[Tuple[str, int]]:
    counts = Counter(file_name for file_name, _ in entries)
    return counts.most_common(limit)


def extract_keywords(entries: Sequence[QuestionEntry], limit: int = 6) -> List[str]:
    counter = Counter()
    for entry in entries:
        tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_./:-]*|[\u4e00-\u9fff]{2,}", entry.text.lower())
        for token in tokens:
            token = token.strip(".,:;/-_")
            if len(token) < 2 or token.isdigit():
                continue
            if token in {"如何", "什么", "为什么", "哪些", "给出", "分析", "总结", "说明", "问题", "方案", "设计", "代码", "方法", "实现"}:
                continue
            counter[token] += 1
    return [word for word, _ in counter.most_common(limit)]


def infer_background(entry: QuestionEntry) -> str:
    text = entry.text
    if re.search(r"报错|异常|错误|失败", text):
        return "这是一个故障排查场景，通常来自线上报错、接口失败或功能异常，需要先确认触发条件。"
    if re.search(r"原理|设计|架构|思想", text):
        return "这是一个源码理解场景，重点不是改代码，而是先建立模块关系和设计认知。"
    if re.search(r"方案|优化|修复|修改", text):
        return "这是一个方案评估场景，重点在比较不同实现路径的改动范围和风险。"
    if re.search(r"接口|api|rest|postman|调用", text, re.I):
        return "这是一个接口落地场景，重点在接口契约、参数组织方式和实现入口。"
    if re.search(r"表|字段|sql|redis|数据库", text, re.I):
        return "这是一个数据模型场景，重点在字段职责、表关系和读写路径。"
    return "这是一个通用技术问题，适合先归入专题，再补充关键对象和处理路径。"


def infer_principle(entry: QuestionEntry) -> str:
    text = entry.text
    if re.search(r"登录|session|下线|权限|认证", text):
        return "核心原理通常围绕身份识别、会话维持、失效判定和异常连接处理展开。"
    if re.search(r"流程|工作流|节点|workitem|审批|表单", text):
        return "核心原理通常围绕流程状态流转、节点处理规则和表单状态同步展开。"
    if re.search(r"接口|api|rest|调用", text, re.I):
        return "核心原理通常是接口契约驱动，外部请求先进入控制层，再进入服务层和底层资源。"
    if re.search(r"表|字段|sql|redis|数据库", text, re.I):
        return "核心原理通常是数据模型驱动，字段定义、读写链路和缓存策略共同决定行为。"
    if re.search(r"日志|监控|性能|统计", text):
        return "核心原理通常是统一采集入口，再按上下文、级别和指标输出到不同目标。"
    if re.search(r"前端|页面|h5|移动端|portal", text):
        return "核心原理通常跨页面渲染、接口请求和终端环境三层，需要分层定位。"
    return "核心原理一般是先明确入口，再梳理调用链和关键状态变化。"


def infer_solution(entry: QuestionEntry) -> str:
    text = entry.text
    if re.search(r"报错|异常|错误|失败", text):
        return "建议先复现现象，再定位入口方法、关键日志和依赖数据，最后再决定修复点与验证步骤。"
    if re.search(r"方案|优化|修复|修改", text):
        return "建议先列出最小改动方案和结构性方案，再比较风险、回归范围和后续维护成本。"
    if re.search(r"接口|api|rest|调用", text, re.I):
        return "建议先固定接口入参与返回结构，再补实现类、鉴权、异常处理和调用示例。"
    if re.search(r"表|字段|sql|redis|数据库", text, re.I):
        return "建议先梳理表关系和字段语义，再看 SQL 路径、索引、缓存和一致性风险。"
    if re.search(r"原理|设计|架构|思想", text):
        return "建议先画出模块关系图，再按主流程梳理核心类、关键方法和扩展点。"
    return "建议先按“入口 -> 关键对象 -> 状态变化 -> 风险点”的顺序复习。"


def infer_key_objects(entry: QuestionEntry) -> str:
    text = entry.text
    objs = []
    patterns = [
        r"[A-Za-z_][A-Za-z0-9_]*Controller",
        r"[A-Za-z_][A-Za-z0-9_]*Service",
        r"[A-Za-z_][A-Za-z0-9_]*Manager",
        r"[A-Za-z_][A-Za-z0-9_]*Impl",
        r"[A-Za-z_][A-Za-z0-9_]*\.java",
        r"[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*",
        r"\b[A-Z][A-Z0-9_]{2,}\b",
        r"rest/[A-Za-z0-9/_-]+",
    ]
    for pattern in patterns:
        for match in re.findall(pattern, text):
            if match not in objs:
                objs.append(match)
    if objs:
        return "优先关注这些对象：" + "、".join(objs[:5]) + "。"
    return "优先关注入口类、核心服务、关键表或接口路径。"


def infer_memory_line(entry: QuestionEntry) -> str:
    text = entry.text
    if re.search(r"报错|异常|错误|失败", text):
        return "一句话记忆：先定位触发条件，再谈修复。"
    if re.search(r"原理|设计|架构|思想", text):
        return "一句话记忆：先懂为什么这样设计，再看代码怎么实现。"
    if re.search(r"表|字段|sql|redis|数据库", text, re.I):
        return "一句话记忆：先弄清数据放哪、怎么变、谁来查。"
    if re.search(r"接口|api|rest|调用", text, re.I):
        return "一句话记忆：接口问题先看契约，再看实现。"
    if re.search(r"登录|session|下线|权限", text):
        return "一句话记忆：先确认用户身份，再确认会话状态。"
    return "一句话记忆：先抓入口，再抓关键对象。"


def build_card(file_name: str, entry: QuestionEntry) -> List[str]:
    return [
        f"#### 复习卡片：{entry.text}",
        "",
        f"- 来源：`{file_name}`",
        f"- 分类：{entry.category}",
        f"- 背景：{infer_background(entry)}",
        f"- 原理：{infer_principle(entry)}",
        f"- 解决思路：{infer_solution(entry)}",
        f"- 关键对象：{infer_key_objects(entry)}",
        f"- 一句话记忆：{infer_memory_line(entry)[7:] if infer_memory_line(entry).startswith('一句话记忆：') else infer_memory_line(entry)}",
        "",
    ]


def build_chapter(name: str, data: dict) -> List[str]:
    entries = [entry for _, entry in data["entries"]]
    file_ranking = top_files(data["entries"], limit=5)
    keywords = extract_keywords(entries, limit=8)
    highlights = choose_highlights(entries, limit=5)
    lines: List[str] = [
        f"## {name}",
        "",
        f"- 本章问题数：{len(entries)}",
        f"- 涉及文件数：{len(data['files'])}",
        f"- 本章复习重点：{FOCUS_HINTS.get(name, '先按场景归纳，再回到实现。')}",
        "",
        "### 一页式记忆",
        "",
    ]
    if keywords:
        lines.append("- 高频关键词：" + "、".join(keywords[:6]))
    lines.append("- 先看什么：" + FOCUS_HINTS.get(name, "先按场景归纳，再回到实现。"))
    lines.append("- 最容易遗漏的点：不要只记结论，要同时记入口、状态变化和验证方法。")
    lines.append("")

    lines.append("### 最值得先看的文件")
    lines.append("")
    for file_name, count in file_ranking:
        lines.append(f"- `{file_name}`：包含 {count} 条本章相关问题")
    lines.append("")

    lines.append("### 高频错误/关注点")
    lines.append("")
    focus_items = []
    joined = " ".join(entry.text for entry in entries[:120])
    if re.search(r"报错|异常|错误|失败", joined):
        focus_items.append("遇到报错不要直接改代码，先固定复现条件和入口方法。")
    if re.search(r"原理|设计|架构|思想", joined):
        focus_items.append("涉及设计讨论时，不要只盯单个方法，要把模块边界一起看。")
    if re.search(r"表|字段|sql|redis|数据库", joined, re.I):
        focus_items.append("涉及数据问题时，字段职责、表关系和缓存策略要一起复习。")
    if re.search(r"接口|api|rest|调用", joined, re.I):
        focus_items.append("接口问题不要只记 URL，还要记鉴权、参数、返回结构和实现入口。")
    if re.search(r"登录|session|下线|权限", joined):
        focus_items.append("登录与会话问题常跨前端提示、后端状态和连接管理三个层次。")
    if not focus_items:
        focus_items.append("本章内容较杂，建议先在 Obsidian 里补标签后再深挖。")
    for item in focus_items[:4]:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("### 重点复习卡片")
    lines.append("")
    for file_name, entry in data["entries"]:
        if entry in highlights:
            lines.extend(build_card(file_name, entry))

    lines.append("### 本章最后记住")
    lines.append("")
    lines.append(f"- {FOCUS_HINTS.get(name, '先按场景归纳，再回到实现。')}")
    lines.append("- 真正落地时，再回到 Obsidian 分类页或单文件页看原始上下文。")
    lines.append("")
    return lines


def build_book(file_summaries, category_data, total_questions: int) -> str:
    generated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_valid = sum(item.valid_count for item in file_summaries)
    ordered = sort_categories(category_data)
    lines: List[str] = [
        "# AI 对话复习电子书 v2",
        "",
        "副标题：更适合背诵与回顾的笔记型电子书",
        "",
        f"生成时间：{generated}",
        "",
        "## 这本书怎么读",
        "",
        "- 第一轮只看每章的“一页式记忆”和“最值得先看的文件”。",
        "- 第二轮看“重点复习卡片”，把问题转成可复述的套路。",
        "- 真正查细节时，再回到 Obsidian 知识库查看具体问题块和原始文件。",
        "",
        "## 全局概览",
        "",
        f"- TXT 文件总数：{len(file_summaries)}",
        f"- 原始问题总数：{total_questions}",
        f"- 清洗后有效问题数：{total_valid}",
        f"- 主专题数：{len(ordered)}",
        "- 建议优先顺序：代码设计与源码分析 -> 问题排查与修复 -> 数据库与数据模型 -> 登录权限与会话",
        "",
        "## 目录",
        "",
    ]
    for idx, (name, data) in enumerate(ordered, start=1):
        lines.append(f"- 第 {idx} 章 {name}：{len(data['entries'])} 个问题")
    lines.append("")
    for name, data in ordered:
        lines.extend(build_chapter(name, data))
    lines.extend([
        "## 附录",
        "",
        "- 第一版电子书仍保留：`out/review_ebook.md` / `out/review_ebook.pdf`",
        "- 第二版定位：更适合复习和背诵；第一版定位：更适合顺读和总览。",
        "- 深入检索入口：`out/obsidian/00-总索引.md`",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    file_summaries, category_data, total_questions = extract_report_data(Path("txt"))
    markdown = build_book(file_summaries, category_data, total_questions)
    MD_OUTPUT.write_text(markdown, encoding="utf-8")
    markdown_to_pdf(markdown, PDF_OUTPUT)
    print(f"Review Markdown v2 已生成：{MD_OUTPUT}")
    print(f"Review PDF v2 已生成：{PDF_OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
