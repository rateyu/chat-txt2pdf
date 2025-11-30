import os
import json
from typing import Optional, Tuple, List

# ----------- 配置 -----------
# 可配置多个输入目录，比如 Codex 日志、Claude 日志、Gemini 日志等
SOURCE_DIRS: List[str] = [
    "/Users/myu/.codex",          # Codex 日志根目录（jsonl）
    "/Users/myu/.claude",     # Claude 日志根目录（jsonl）
    "/Users/myu/.gemini",     # Gemini 日志根目录（json）
]

OUTPUT_DIR = "/Users/myu/chat-his"     # 输出：生成的 txt 根目录
# ---------------------------


def ensure_dir(path: str):
    if path and not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def try_parse_nested_json(s: str) -> str:
    """
    针对 payload.output 是 JSON 字符串的情况：
    例如："{\"output\": \"Date: 2025-11-17\\nUser: ...\", \"metadata\": {...}}"
    """
    try:
        nested = json.loads(s)
        if isinstance(nested, dict):
            for key in ("output", "content", "text", "message"):
                v = nested.get(key)
                if isinstance(v, str) and v.strip():
                    return v
    except Exception:
        pass
    return s


def extract_from_claude_message(msg: dict) -> Tuple[Optional[str], str]:
    """
    解析 Claude 风格的 message 结构：
    {
      "message": {
        "role": "assistant" | "user",
        "content": [
          {"type": "text", "text": "..."},
          {"type": "tool_use", "input": {"prompt": "..."}}
        ]
      }
    }
    """
    role = msg.get("role")

    content = msg.get("content")
    texts: List[str] = []

    # content 可能是 list，也可能是 string
    if isinstance(content, list):
        for part in content:
            if not isinstance(part, dict):
                continue
            p_type = part.get("type")

            # 纯文本
            if p_type == "text":
                text_val = part.get("text")
                if isinstance(text_val, str) and text_val.strip():
                    texts.append(text_val)

            # tool_use 里通常有 input.prompt，可以视为用户请求的完整描述
            elif p_type == "tool_use":
                input_obj = part.get("input", {})
                if isinstance(input_obj, dict):
                    prompt = input_obj.get("prompt")
                    if isinstance(prompt, str) and prompt.strip():
                        texts.append(prompt)
                    else:
                        # 没 prompt，就把整个 input json 打出来（如不需要可删掉）
                        try:
                            texts.append(json.dumps(input_obj, ensure_ascii=False, indent=2))
                        except Exception:
                            pass

    elif isinstance(content, str):
        if content.strip():
            texts.append(content)

    if texts:
        return role, "\n\n".join(texts)

    return role, ""


def extract_from_gemini_message(obj: dict) -> Tuple[Optional[str], str]:
    """
    解析 Gemini 风格的消息：
    {
      "role": "user" | "model",
      "parts": [
        {"text": "..."},
        {"text": "..."}
      ]
    }
    """
    role = obj.get("role")
    parts = obj.get("parts")
    texts: List[str] = []

    if isinstance(parts, list):
        for p in parts:
            if not isinstance(p, dict):
                continue
            t = p.get("text")
            if isinstance(t, str) and t.strip():
                texts.append(t)

    if texts:
        return role, "\n\n".join(texts)

    return role, ""


def extract_text(obj: dict) -> Tuple[Optional[str], str]:
    """
    从一行/一个对象中提取 (role, text)
    兼容：
      - Codex 风格：顶层 role/content/text/payload.output
      - Claude 风格：顶层 message.role / message.content
      - Gemini 风格：顶层 role/parts[*].text
    """

    # 1️⃣ Claude: 顶层有 message
    msg = obj.get("message")
    if isinstance(msg, dict):
        role, text = extract_from_claude_message(msg)
        if text.strip():
            return role, text
        # 解析不到再退回其他逻辑

    # 2️⃣ Gemini: 顶层有 role + parts
    if isinstance(obj.get("parts"), list) and "role" in obj:
        role, text = extract_from_gemini_message(obj)
        if text.strip():
            return role, text

    # 3️⃣ Codex / 通用：顶层 role / content / text
    role = obj.get("role")

    for key in ("content", "text"):
        v = obj.get(key)
        if isinstance(v, str) and v.strip():
            return role, v

    # 4️⃣ Codex: payload 中
    payload = obj.get("payload")
    if isinstance(payload, dict):

        # 常规 content/text/message
        for key in ("content", "text", "message"):
            v = payload.get(key)
            if isinstance(v, str) and v.strip():
                return role, v

        # payload.output 再套一层 JSON 字符串
        v = payload.get("output")
        if isinstance(v, str) and v.strip():
            parsed = try_parse_nested_json(v)
            return role, parsed

    # 5️⃣ 整体都没找到可用文本
    return role, ""


def write_messages_to_txt(messages: List[Tuple[Optional[str], str]], txt_path: str):
    """
    把 messages 写入 txt 文件，并在文件开头写“问题索引（User Questions）”
    messages: [(role, text), ...]
    """
    questions: List[str] = []

    for role, text in messages:
        if role and isinstance(role, str) and role.lower() == "user":
            first_line = text.strip().split("\n")[0]
            if first_line:
                questions.append(first_line)

    ensure_dir(os.path.dirname(txt_path))

    with open(txt_path, "w", encoding="utf-8") as out:

        # 先写问题索引
        if questions:
            out.write("============ 问题索引（User Questions） ============\n")
            for i, q in enumerate(questions, 1):
                out.write(f"{i}. {q}\n")
            out.write("====================================================\n\n\n")

        # 再写完整内容
        for role, text in messages:
            if role:
                out.write(f"{role.upper()}:\n{text}\n\n")
            else:
                out.write(text + "\n\n")


def process_jsonl_file(jsonl_path: str, txt_path: str):
    """处理 Codex / Claude 样式的 .jsonl 文件"""
    messages: List[Tuple[Optional[str], str]] = []

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                obj = json.loads(line)
            except Exception:
                continue

            role, text = extract_text(obj)
            if not text.strip():
                continue

            messages.append((role, text))

    write_messages_to_txt(messages, txt_path)


def process_json_file(json_path: str, txt_path: str):
    """处理 Gemini 样式的 .json 文件"""
    messages: List[Tuple[Optional[str], str]] = []

    with open(json_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception:
            return

    objs: List[dict] = []

    # 顶层就是一个列表：直接当作消息列表
    if isinstance(data, list):
        objs = [x for x in data if isinstance(x, dict)]

    # 顶层是 dict：尝试在常见字段中找消息列表
    elif isinstance(data, dict):
        for key in ("history", "contents", "messages", "conversation", "items"):
            val = data.get(key)
            if isinstance(val, list):
                objs = [x for x in val if isinstance(x, dict)]
                break

        # 如果没找到，就退回把整个 dict 当成一个对象试试
        if not objs:
            objs = [data]

    # 遍历每个对象，考虑 Gemini 的 candidates 等结构
    for obj in objs:
        # 如果有 candidates，则尝试从 candidates[*].content 中取
        if isinstance(obj, dict) and "candidates" in obj and isinstance(obj["candidates"], list):
            for cand in obj["candidates"]:
                if not isinstance(cand, dict):
                    continue
                content = cand.get("content")
                if isinstance(content, dict):
                    role, text = extract_text(content)
                    if text.strip():
                        messages.append((role, text))
        else:
            role, text = extract_text(obj)
            if text.strip():
                messages.append((role, text))

    write_messages_to_txt(messages, txt_path)


def convert_one_source_dir(source_dir: str, output_root: str):
    """处理单个输入目录，输出到：output_root/<源目录名>/..."""
    if not os.path.isdir(source_dir):
        print(f"[警告] 跳过：{source_dir}（不是有效目录）")
        return

    source_abs = os.path.abspath(source_dir)
    base_name = os.path.basename(source_abs.rstrip(os.sep)) or "root"

    print(f"\n=== 开始扫描目录：{source_dir} (输出子目录名：{base_name}) ===")

    for root, dirs, files in os.walk(source_dir):
        for filename in files:
            jsonl = filename.endswith(".jsonl")
            jsonf = filename.endswith(".json")

            if not (jsonl or jsonf):
                continue

            input_path = os.path.join(root, filename)

            # 相对路径
            relative_path = os.path.relpath(input_path, source_dir)
            # 输出路径：export/<base_name>/<relative_path>.txt
            txt_relative = os.path.join(base_name, relative_path)
            txt_relative = txt_relative.rsplit(".", 1)[0] + ".txt"
            txt_output_path = os.path.join(output_root, txt_relative)

            ensure_dir(os.path.dirname(txt_output_path))

            if jsonl:
                print(f"转换(jsonl)：{input_path} → {txt_output_path}")
                process_jsonl_file(input_path, txt_output_path)
            else:
                print(f"转换(json)：{input_path} → {txt_output_path}")
                process_json_file(input_path, txt_output_path)


def batch_convert_multiple(source_dirs: List[str], output_root: str):
    ensure_dir(output_root)
    for src in source_dirs:
        convert_one_source_dir(src, output_root)
    print("\n全部转换完成！总输出目录：", output_root)


if __name__ == "__main__":
    batch_convert_multiple(SOURCE_DIRS, OUTPUT_DIR)
