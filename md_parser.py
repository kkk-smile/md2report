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

    标题规则（固定，不再自动检测层级）：
      #   → 一级标题 h1（黑体，不加粗）
      ##  → 二级标题 h2（宋体，加粗）
      ### → 三级标题 h3（宋体，加粗）

    封面跳过策略：
      正文从第一个"数字开头的标题"开始（如 # 1. 或 ## 1.）
      其他标题（文件名、封面大标题等）继续跳过
    """
    blocks = []
    lines  = md_text.splitlines()

    in_code    = False
    code_lines = []
    skip_cover = True

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

        # ── 跳过封面 ─────────────────────────────────────────────────
        # 遇到"数字开头的标题"才算正文开始，其余标题行继续跳过
        if skip_cover:
            m = re.match(r'^(#{1,3})\s+(.*)', line)
            if m:
                title_text = m.group(2).strip()
                # 数字开头（1. 或 1 ）视为正文章节标题
                if re.match(r'^\d+[\.\s]', title_text):
                    skip_cover = False
                    # 继续往下解析这一行
                else:
                    continue  # 封面标题，跳过
            else:
                continue  # 封面内容，跳过

        # ── 忽略分割线 ───────────────────────────────────────────────
        if stripped == '---':
            continue

        # ── 标题映射（固定规则）──────────────────────────────────────
        # #   → h1，## → h2，### → h3，#### → h3
        h3_plus = re.match(r'^#{3,}\s+(.*)', line)
        h2      = re.match(r'^##\s+(.*)',    line)
        h1      = re.match(r'^#\s+(.*)',     line)

        if h3_plus:
            blocks.append({"type": "h3", "text": h3_plus.group(1).strip()})
        elif h2:
            blocks.append({"type": "h2", "text": h2.group(1).strip()})
        elif h1:
            blocks.append({"type": "h1", "text": h1.group(1).strip()})
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
