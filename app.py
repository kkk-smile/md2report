"""
md2report - Flask 主入口
"""

import os
import sys

# 让 report_utils 可以从上级目录导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, send_file, render_template, jsonify
import io

from md_parser import parse_md, parse_cover
from report_builder import build_docx

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2MB 上限


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert():
    data = request.get_json(force=True)

    md_text = data.get("md_text", "").strip()
    if not md_text:
        return jsonify({"error": "内容不能为空"}), 400

    cover_type = data.get("cover_type", "personal")

    if cover_type == "group":
        # members: [{"name": "张三", "sid": "230100001"}, ...]
        raw_members = data.get("members", [])
        members = [(m.get("name", ""), m.get("sid", "")) for m in raw_members]
        cover = {
            "type": "group",
            "members": members,
            "course": data.get("course", ""),
            "topic": data.get("topic", ""),
            "major": data.get("major", ""),
            "teacher": data.get("teacher", ""),
        }
    else:
        cover = {
            "type": "personal",
            "name": data.get("name", ""),
            "sid": data.get("sid", ""),
            "course": data.get("course", ""),
            "topic": data.get("topic", ""),
            "major": data.get("major", ""),
            "teacher": data.get("teacher", ""),
        }

    # 从 MD 自动提取封面信息，表单填写的优先级更高（非空时覆盖）
    md_cover = parse_cover(md_text)
    for key in ('course', 'topic', 'name', 'sid', 'major', 'teacher'):
        if not cover.get(key) and md_cover.get(key):
            cover[key] = md_cover[key]

    blocks = parse_md(md_text)
    fmt = data.get("fmt")  # 格式参数，可选
    docx_bytes = build_docx(cover, blocks, fmt)

    filename = f"课程设计报告-{cover.get('name') or '小组'}.docx"

    return send_file(
        io.BytesIO(docx_bytes),
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=filename,
    )


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=False, host="0.0.0.0", port=port)
