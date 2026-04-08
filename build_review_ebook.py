import datetime
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from summarize_txt_reports import (
    OUT_DIR,
    QuestionEntry,
    choose_highlights,
    extract_report_data,
    markdown_to_pdf,
)


MD_OUTPUT = OUT_DIR / "review_ebook.md"
PDF_OUTPUT = OUT_DIR / "review_ebook.pdf"


COMMON_STOPWORDS = {
    "如何", "什么", "为什么", "哪些", "这个", "那个", "一下", "继续", "给出", "分析", "总结", "说明",
    "问题", "方案", "设计", "代码", "方法", "功能", "实现", "相关", "核心", "以及", "可以", "还有",
    "一个", "现在", "这里", "时候", "根据", "框架", "使用", "需要", "进行", "对于", "不是", "然后",
    "通过", "是否", "因为", "怎么", "哪里", "一下", "一下子", "中的", "如果", "时候", "并且", "已经",
    "目前", "希望", "这种", "这样", "这些", "那些", "一下吧", "一下呢",
}


CHAPTER_INTRO = {
    "表单与流程": "这一章适合复习流程流转、公文处理、表单建模和审批节点之间的关系，重点是把业务动作和系统状态变更对应起来。",
    "接口与集成": "这一章适合复习接口调用链、入参与出参设计、第三方系统对接边界，以及接口落地时常见的兼容问题。",
    "前端与移动端": "这一章适合复习页面报错、H5 与移动端兼容、Portal 主题和前后端联动问题，重点是定位表现层与请求链路的交界点。",
    "登录权限与会话": "这一章适合复习登录认证、会话维持、被迫下线和权限识别，重点是识别用户、会话失效和异常退出的触发机制。",
    "日志与监控": "这一章适合复习日志体系、监控埋点、性能统计和排障可观测性，重点是统一口径、提升定位效率。",
    "数据库与数据模型": "这一章适合复习表结构、字段语义、缓存关系、SQL 性能和数据一致性，重点是数据从哪里来、怎么存、怎么查。",
    "代码设计与源码分析": "这一章适合复习模块架构、核心类方法、调用链和设计思想，重点是先抓主干，再看细节实现。",
    "运维与自动化": "这一章适合复习脚本化处理、仓库工作流、导出转换、知识库维护和工具链自动化，重点是提升重复工作的复用度。",
    "时间与业务规则": "这一章适合复习工作日、截止时间、年份边界和特殊日期规则配置，重点是业务规则如何映射到系统配置。",
    "问题排查与修复": "这一章适合复习报错定位、故障排查、修复路径和回归验证，重点是从现象到根因再到修复闭环。",
    "其他": "这一章收纳暂未被稳定归类但仍有价值的问题，适合作为补充阅读和后续二次整理入口。",
}


MEMORY_LINES = {
    "表单与流程": "记忆点：先确认流程节点和表状态，再判断业务动作是否真的改变了流程引擎中的工作项。",
    "接口与集成": "记忆点：先看接口契约，再看实现类，最后核对参数和返回结构是否匹配业务预期。",
    "前端与移动端": "记忆点：先分清是前端渲染问题、接口返回问题，还是移动端环境兼容问题。",
    "登录权限与会话": "记忆点：先确认谁代表用户身份，再确认 session、cookie、连接状态分别何时失效。",
    "日志与监控": "记忆点：日志不是越多越好，关键是统一入口、带上下文、能支持快速定位。",
    "数据库与数据模型": "记忆点：表结构问题先看字段职责，性能问题先看 SQL 路径，一致性问题先看写入链路。",
    "代码设计与源码分析": "记忆点：先抓核心类和主调用链，再梳理扩展点和特殊分支。",
    "运维与自动化": "记忆点：凡是重复执行三次以上的动作，都值得收敛成脚本或固定工作流。",
    "时间与业务规则": "记忆点：所有时间规则都要先明确边界年份、默认值和配置入口。",
    "问题排查与修复": "记忆点：先复现、再定位、后修复，最后一定要补回归验证路径。",
    "其他": "记忆点：未分类问题先按场景打标签，再决定是否值得沉淀成正式专题。",
}


def category_sort_key(item: Tuple[str, dict]) -> Tuple[int, str]:
    name, data = item
    return (-len(data["entries"]), name)


def extract_keywords(entries: Sequence[QuestionEntry], limit: int = 8) -> List[str]:
    counter = Counter()
    for entry in entries:
        text = entry.text.lower()
        tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_./:-]*|[\u4e00-\u9fff]{2,}", text)
        for token in tokens:
            token = token.strip(".,:;/-_")
            if len(token) < 2:
                continue
            if token in COMMON_STOPWORDS:
                continue
            if token.isdigit():
                continue
            counter[token] += 1
    return [word for word, _ in counter.most_common(limit)]


def build_learning_goals(category: str, entries: Sequence[QuestionEntry]) -> List[str]:
    texts = " ".join(entry.text for entry in entries[:80])
    goals: List[str] = []
    if re.search(r"原理|设计|架构|思想", texts):
        goals.append("先搞清楚这一类问题背后的设计原理和模块关系。")
    if re.search(r"方法|类|源码|实现类|核心类", texts):
        goals.append("定位关键类、核心方法和主调用链，建立源码地图。")
    if re.search(r"报错|异常|错误|排查|原因", texts):
        goals.append("建立从现象到根因的排查顺序，避免只盯单点代码。")
    if re.search(r"方案|修复|优化|修改", texts):
        goals.append("比较方案差异，明确改动范围、风险点和回归验证路径。")
    if re.search(r"表|字段|sql|redis|数据库", texts):
        goals.append("把数据模型、字段职责和读写关系梳理清楚。")
    if re.search(r"接口|api|rest|调用|postman", texts):
        goals.append("把接口契约、入参、返回值和实现入口串起来理解。")
    if not goals:
        goals.append("把高频问题收敛成稳定的复习框架，减少回翻原始记录的次数。")
    return goals[:4]


def build_core_points(category: str, entries: Sequence[QuestionEntry]) -> List[str]:
    keywords = extract_keywords(entries, limit=10)
    points: List[str] = []
    if keywords:
        points.append("高频关键词：" + "、".join(keywords[:6]))
    texts = " ".join(entry.text for entry in entries[:80])
    if category == "代码设计与源码分析":
        points.extend([
            "复习顺序建议按“模块职责 -> 核心类 -> 关键方法 -> 扩展点”展开。",
            "同类问题里经常同时出现“原理说明”和“代码位置定位”，复习时两者要配套看。",
        ])
    elif category == "问题排查与修复":
        points.extend([
            "这一类问题不要只记修复动作，更要记住触发条件和排查顺序。",
            "复习时优先沉淀“现象 -> 根因 -> 修复 -> 验证”四段式模板。",
        ])
    elif category == "数据库与数据模型":
        points.extend([
            "同一主题经常涉及表结构、字段含义、SQL 性能和缓存关系，需要放在同一个视角里看。",
            "复习时优先建立“数据来源 -> 存储位置 -> 查询路径 -> 一致性风险”的框架。",
        ])
    elif category == "登录权限与会话":
        points.extend([
            "重点不是记提示文案，而是弄清谁代表用户身份、谁控制会话失效、谁触发被迫下线。",
            "这类问题通常跨前端提示、后端状态和连接管理三个层次。",
        ])
    else:
        if re.search(r"报错|异常|错误", texts):
            points.append("这一章里有明显的排障内容，复习时要把异常现象和根因拆开记。")
        if re.search(r"原理|设计|架构", texts):
            points.append("这一章里有明显的设计讨论内容，复习时要先画出模块关系再看细节。")
        if re.search(r"接口|api|rest", texts):
            points.append("这一章里有接口调用类内容，适合按接口入口、参数、实现类的顺序回顾。")
    points.append(MEMORY_LINES.get(category, "记忆点：先从场景入手，再回到实现细节。"))
    deduped = []
    seen = set()
    for point in points:
        if point not in seen:
            deduped.append(point)
            seen.add(point)
    return deduped[:5]


def group_entries_by_file(entries: Sequence[Tuple[str, QuestionEntry]]) -> Dict[str, List[QuestionEntry]]:
    grouped: Dict[str, List[QuestionEntry]] = {}
    for file_name, entry in entries:
        grouped.setdefault(file_name, []).append(entry)
    return grouped


def build_review_card(file_name: str, entry: QuestionEntry) -> List[str]:
    card = [
        f"#### 问题卡片：{entry.text}",
        "",
        f"- 来源文件：`{file_name}`",
        f"- 主题分类：{entry.category}",
        f"- 背景：这类提问通常来自具体业务问题、源码阅读任务或故障排查场景，需要把原始问题转成稳定知识点。",
        f"- 总结要点：{entry.summary}",
        f"- 复习提示：{entry.review_tip}",
    ]

    if re.search(r"原理|设计|架构|思想", entry.text):
        card.append("- 推荐复习路径：先理解设计目标和模块关系，再定位核心实现类和调用链。")
    elif re.search(r"报错|异常|错误|原因", entry.text):
        card.append("- 推荐复习路径：先确认报错触发条件，再梳理根因、修复动作和验证方法。")
    elif re.search(r"表|字段|sql|redis", entry.text, re.I):
        card.append("- 推荐复习路径：先看数据结构和字段职责，再看查询或写入链路。")
    elif re.search(r"接口|rest|api|调用", entry.text, re.I):
        card.append("- 推荐复习路径：先看接口契约，再看实现入口和参数流转。")
    else:
        card.append("- 推荐复习路径：先按场景理解问题，再补充相关实现入口和限制条件。")
    card.append("")
    return card


def build_chapter(name: str, data: dict) -> List[str]:
    entries = [entry for _, entry in data["entries"]]
    grouped = group_entries_by_file(data["entries"])
    highlights = choose_highlights(entries, limit=6)
    lines: List[str] = []
    lines.append(f"## {name}")
    lines.append("")
    lines.append(CHAPTER_INTRO.get(name, data["summary"]))
    lines.append("")
    lines.append("### 本章学习目标")
    lines.append("")
    for goal in build_learning_goals(name, entries):
        lines.append(f"- {goal}")
    lines.append("")

    lines.append("### 本章核心知识点")
    lines.append("")
    for point in build_core_points(name, entries):
        lines.append(f"- {point}")
    lines.append("")

    lines.append("### 重点问题卡片")
    lines.append("")
    for file_name, entry in data["entries"]:
        if entry in highlights:
            lines.extend(build_review_card(file_name, entry))

    lines.append("### 本章复习路线")
    lines.append("")
    top_files = sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))[:5]
    for file_name, file_entries in top_files:
        lines.append(f"- 先看 `{file_name}`：该文件包含 {len(file_entries)} 条与本章相关的问题。")
    lines.append("- 再回到 Obsidian 分类页，按问题卡片逐个补充关键代码位置或解决步骤。")
    lines.append("")
    return lines


def build_book(file_summaries, category_data, total_questions: int) -> str:
    generated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_valid = sum(item.valid_count for item in file_summaries)
    categories_by_count = sorted(
        [(name, data) for name, data in category_data.items() if data["entries"]],
        key=category_sort_key,
    )

    lines: List[str] = []
    lines.append("# AI 对话复习电子书")
    lines.append("")
    lines.append("副标题：基于 TXT 归档内容生成的章节式复习材料")
    lines.append("")
    lines.append(f"生成时间：{generated}")
    lines.append("")

    lines.append("## 阅读说明")
    lines.append("")
    lines.append("- 这不是原始归档导出，而是按复习场景重组后的章节式材料。")
    lines.append("- 阅读顺序建议：先看“总体地图”，再按主题章节学习，最后通过 Obsidian 继续深挖。")
    lines.append("- 如果某个章节与你当前工作最接近，可以直接跳过其他章节，只看对应专题。")
    lines.append("")

    lines.append("## 总体地图")
    lines.append("")
    lines.append(f"- TXT 文件总数：{len(file_summaries)}")
    lines.append(f"- 原始问题总数：{total_questions}")
    lines.append(f"- 清洗后有效问题数：{total_valid}")
    lines.append(f"- 核心主题数量：{len(categories_by_count)}")
    lines.append("- 推荐优先阅读顺序：代码设计与源码分析 -> 问题排查与修复 -> 数据库与数据模型 -> 登录权限与会话")
    lines.append("")

    lines.append("## 目录")
    lines.append("")
    for idx, (name, data) in enumerate(categories_by_count, start=1):
        lines.append(f"- 第 {idx} 章 {name}：{len(data['entries'])} 个问题")
    lines.append("")

    lines.append("## 复习建议")
    lines.append("")
    lines.append("- 第一次阅读只抓“本章学习目标”和“核心知识点”，先建立全局框架。")
    lines.append("- 第二次阅读重点看“问题卡片”，把抽象问题转成你能复述的解决套路。")
    lines.append("- 真正需要落地时，再从 Obsidian 中跳回对应分类页或单文件页定位原始上下文。")
    lines.append("")

    for name, data in categories_by_count:
        lines.extend(build_chapter(name, data))

    lines.append("## 附录：回到知识库")
    lines.append("")
    lines.append("- 总索引：`out/obsidian/00-总索引.md`")
    lines.append("- 分类页：`out/obsidian/分类汇总/`")
    lines.append("- 文件页：`out/obsidian/逐文件摘要/`")
    lines.append("- 使用策略：电子书负责顺读复习，Obsidian 负责跳转检索和持续沉淀。")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    file_summaries, category_data, total_questions = extract_report_data(Path("txt"))
    markdown = build_book(file_summaries, category_data, total_questions)
    MD_OUTPUT.write_text(markdown, encoding="utf-8")
    markdown_to_pdf(markdown, PDF_OUTPUT)
    print(f"Review Markdown 已生成：{MD_OUTPUT}")
    print(f"Review PDF 已生成：{PDF_OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
