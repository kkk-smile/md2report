"""
MD → 中间结构解析器
输出统一的 block 列表，方便后续扩展其他格式（txt 等）

block 结构：
  {"type": "h1"|"h2"|"h3"|"h4"|"body"|"code"|"blank", "text": str}
  代码块额外有 "lines": [str, ...]

封面提取：
  parse_cover(md_text) → dict  从 MD 开头的 **字段：** 值 格式提取封面信息
"""

import re


# ── 封面字段映射 ──────────────────────────────────────────────────────
_COVER_FIELD_MAP = {
    '课程名称': 'course',
    '题目':     'topic',
    '题　　目': 'topic',
    '学生姓名': 'name',
    '学号':     'sid',
    '学　　号': 'sid',
    '专业班级': 'major',
    '指导教师': 'teacher',
    '日期':     'date',
    '日　　期': 'date',
}


def parse_cover(md_text: str) -> dict:
    """
    从 MD 文本开头提取封面信息。
    识别格式：**字段：** 值  或  **字段：**值
    返回 dict，key 为英文字段名（course/topic/name/sid/major/teacher）
    """
    cover = {}
    for line in md_text.splitlines():
        # 匹配 **字段：** 值
        m = re.match(r'^\*\*(.+?)[:：]\*\*\s*(.*)', line.strip())
        if m:
            raw_key = m.group(1).strip()
            value   = m.group(2).strip()
            en_key  = _COVER_FIELD_MAP.get(raw_key)
            if en_key:
                cover[en_key] = value
    return cover


def parse_md(md_text: str) -> list:
    """
    将 Markdown 文本解析为 block 列表。
    封面跳过策略：第一个 # 标题之前的所有内容全部跳过（不管有没有 ---）。
    标题层级自动适配：检测正文最浅标题层级，自动偏移映射到 h1/h2/h3。
    """
    blocks = []
    lines  = md_text.splitlines()

    # 自动检测正文最浅标题层级（第一个 # 标题开始算）
    min_level = 4
    found_first = False
    for l in lines:
        if not found_first and re.match(r'^#{1,4}\s+', l):
            found_first = True
        if found_first:
            m = re.match(r'^(#{1,4})\s+', l)
            if m:
                min_level = min(min_level, len(m.group(1)))
    if min_level == 4:
        min_level = 1
    level_offset = min_level - 1

    in_code    = False
    code_lines = []
    skip_cover = True  # 跳过第一个标题之前的所有内容

    for line in lines:
        # ── 代码块 ──────────────────────────────────────────────────
        if line.strip().startswith("```"):
            if not in_code:
                in_code = True
                code_lines = []
            else:
                in_code = False
                if code_lines:
                    blocks.append({"type": "code", "lines": code_lines})
            continue

        if in_code:
            code_lines.append(line)
            continue

        stripped = line.strip()

        # ── 跳过封面：遇到第一个标题才开始解析 ──────────────────────
        if skip_cover:
            if re.match(r'^#{1,4}\s+', line):
                skip_cover = False
                # 如果这个标题是封面大标题（含"课程设计"），跳过它
                title_text = re.sub(r'^#{1,4}\s+', '', line).strip()
                if '课程设计' in title_text or '莆田学院' in title_text:
                    continue
                # 否则是正文第一个标题，继续往下解析
            else:
                continue

        # ── 忽略分割线 ───────────────────────────────────────────────
        if stripped == '---':
            continue

        # ── 标题映射 ─────────────────────────────────────────────────
        h4 = re.match(r'^####\s+(.*)', line)
        h3 = re.match(r'^###\s+(.*)',  line)
        h2 = re.match(r'^##\s+(.*)',   line)
        h1 = re.match(r'^#\s+(.*)',    line)

        if h4:
            raw_level, text = 4, h4.group(1).strip()
        elif h3:
            raw_level, text = 3, h3.group(1).strip()
        elif h2:
            raw_level, text = 2, h2.group(1).strip()
        elif h1:
            raw_level, text = 1, h1.group(1).strip()
        else:
            raw_level, text = 0, None

        if raw_level > 0:
            mapped = max(1, min(raw_level - level_offset, 3))
            blocks.append({"type": f"h{mapped}", "text": text})
            continue
        elif stripped == "":
            blocks.append({"type": "blank"})
        else:
            text = line.lstrip('　').strip()
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
            text = re.sub(r'\*(.+?)\*',     r'\1', text)
            text = re.sub(r'`(.+?)`',        r'\1', text)
            text = text.strip()
            if text:
                blocks.append({"type": "body", "text": text})

    return blocks
