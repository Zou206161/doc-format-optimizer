"""端到端：本科毕业论文格式 + 用户真实论文文档。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests

BASE = os.path.dirname(os.path.abspath(__file__))
API = "http://localhost:8000/api"

USER_DOC = os.path.join(BASE, "user_real_doc.docx")

THESIS_REQS = """本科毕业论文格式要求：

纸张型号：A4纸。
页边距：天头(上)20mm，地角(下)15mm，订口(左)25mm，翻口(右)20mm。

字体要求：
(1)论文标题2号黑体加粗、居中。
(7)正文文字另起页，论文标题用3号黑体，正文文字一般用小4 号宋体，每段首起空两个格，单倍行距。
(8)正文文中标题
一级标题：标题序号为"一、"， 4号黑体，独占行，末尾不加标点符号。
二级标题：标题序号为"(一)"与正文字号相同，独占行，末尾不加标点符号。
三级标题：标题序号为" 1. "与正文字号、字体相同。
(11)参考文献：另起页，4号黑体，内容为5号宋体。
中文字体正文使用宋体，大标题使用黑体。英文用Times New Roman字体。"""

print("=" * 70)
print("  端到端测试：本科毕业论文格式 + 真实论文")
print("=" * 70)

PASS = 0
FAIL = 0

def check(name, condition, expected="", actual=""):
    global PASS, FAIL
    if condition:
        print(f"  ✅ {name}")
        PASS += 1
    else:
        print(f"  ❌ {name}")
        if expected: print(f"     期望: {expected}")
        if actual: print(f"     实际: {actual}")
        FAIL += 1

# Step 1: Parse requirements from text
print("\n【Step 1】文字格式要求解析")
r = requests.post(f"{API}/rules/from-text", data={
    "text": THESIS_REQS,
    "preset_id": "undergraduate_thesis",
})
print(f"  状态: {r.status_code}")
if r.status_code != 200:
    print(f"  错误: {r.text}")
    sys.exit(1)
result = r.json()
rules = result["rule_set"]
sources = result.get("sources", {})
print(f"  状态: {r.status_code}")
print(f"  样式数: {len(rules['styles'])}")
print(f"  来源标注: {len(sources)}项")

dl = rules["document_level"]
check("A4纸张", abs(dl["page_width"] - 595.3) < 1)
check("上边距20mm≈56.7pt", abs(dl["margin_top"] - 56.7) < 3, "≈56.7pt", f"{dl['margin_top']}pt")
check("下边距15mm≈42.5pt", abs(dl["margin_bottom"] - 42.5) < 3, "≈42.5pt", f"{dl['margin_bottom']}pt")
check("左边距25mm≈70.9pt", abs(dl["margin_left"] - 70.9) < 3, "≈70.9pt", f"{dl['margin_left']}pt")
check("右边距20mm≈56.7pt", abs(dl["margin_right"] - 56.7) < 3, "≈56.7pt", f"{dl['margin_right']}pt")

t = rules["styles"]["Title"]
check("Title: 黑体", t["font"]["font_name_east_asia"] == "黑体")
check("Title: 二号(22pt)", t["font"]["font_size"] == 22.0, "22pt", f"{t['font']['font_size']}pt")
check("Title: 加粗", t["font"]["bold"] == True)
check("Title: 居中", t["paragraph"]["alignment"] == "center")

h1 = rules["styles"]["Heading1"]
check("H1: 黑体", h1["font"]["font_name_east_asia"] == "黑体")
check("H1: 四号(14pt)", h1["font"]["font_size"] == 14.0, "14pt", f"{h1['font']['font_size']}pt")
check("H1: 加粗", h1["font"]["bold"] == True)

h2 = rules["styles"]["Heading2"]
check("H2: 小四号(12pt)", h2["font"]["font_size"] == 12.0, "12pt", f"{h2['font']['font_size']}pt")

b = rules["styles"]["Body"]
check("Body: 宋体", b["font"]["font_name_east_asia"] == "宋体")
check("Body: 小四号(12pt)", b["font"]["font_size"] == 12.0, "12pt", f"{b['font']['font_size']}pt")
check("Body: 单倍行距", b["paragraph"]["line_spacing"] == 1.0, "1.0", str(b["paragraph"]["line_spacing"]))
check("Body: 首行缩进24pt", b["paragraph"]["first_line_indent"] == 24.0)

ref = rules["styles"]["Reference"]
check("Reference: 五号(10.5pt)", ref["font"]["font_size"] == 10.5, "10.5pt", f"{ref['font']['font_size']}pt")
check("Reference: 宋体", ref["font"]["font_name_east_asia"] == "宋体")
check("Reference: 悬挂缩进24pt", ref["paragraph"]["left_indent"] == 24.0)

# Step 2: Generate document
print("\n【Step 2】文档生成")
import json
rules_json_str = json.dumps(rules, ensure_ascii=False)
with open(USER_DOC, "rb") as f:
    files = {"file": ("论文.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    data = {"rules_json": rules_json_str, "skip_optimization": "true"}
    r = requests.post(f"{API}/optimize/generate", files=files, data=data)

print(f"  状态: {r.status_code}")
print(f"  文件大小: {len(r.content)} bytes")
check("生成成功", r.status_code == 200)
check("文件非空", len(r.content) > 30000)

out_path = os.path.join(BASE, "thesis_final_output.docx")
with open(out_path, "wb") as f:
    f.write(r.content)

# Step 3: Verify output
print("\n【Step 3】成品文档验证")
from src.modules.parser import parse_document

v = parse_document(out_path)
check("成品纸张=A4", abs(v.page_width - 595.3) < 1)
check("成品上边距", v.margin_top is not None and abs(v.margin_top - 56.7) < 3)
check("成品下边距", v.margin_bottom is not None and abs(v.margin_bottom - 42.5) < 3)
check("成品左边距", v.margin_left is not None and abs(v.margin_left - 70.9) < 3)
check("成品右边距", v.margin_right is not None and abs(v.margin_right - 56.7) < 3)

# Find key paragraphs
title_p = v.paragraphs[0]
check("标题: 黑体", title_p.font.font_name_east_asia == "黑体")
check("标题: 22pt", title_p.font.font_size == 22.0, "22pt", f"{title_p.font.font_size}pt")
check("标题: 加粗", title_p.font.bold == True)
check("标题: 居中", str(title_p.paragraph.alignment).lower().endswith("center"))

# Find H1 paragraph
h1_p = None
for p in v.paragraphs:
    if p.text.strip() == "引言":
        h1_p = p
        break
if h1_p:
    check("H1引言: 黑体", h1_p.font.font_name_east_asia == "黑体")
    check("H1引言: 14pt", h1_p.font.font_size == 14.0, "14pt", f"{h1_p.font.font_size}pt")
    check("H1引言: 加粗", h1_p.font.bold == True)

# Find a body paragraph
body_p = None
for p in v.paragraphs:
    if len(p.text) > 50 and "人工智能" in p.text and not p.is_heading:
        body_p = p
        break
if body_p:
    check("正文: 宋体", body_p.font.font_name_east_asia == "宋体")
    check("正文: 12pt", body_p.font.font_size == 12.0, "12pt", f"{body_p.font.font_size}pt")
    check("正文: 单倍行距", body_p.paragraph.line_spacing == 1.0, "1.0", str(body_p.paragraph.line_spacing))
    check("正文: 首行缩进24pt", body_p.paragraph.first_line_indent == 24.0)

# References
ref_start = None
ref_items = []
for i, p in enumerate(v.paragraphs):
    if p.text.strip() == "参考文献":
        ref_start = i
        continue
    if ref_start is not None and p.text.strip():
        ref_items.append(p)

check("找到参考文献标题", ref_start is not None)
check(f"参考文献条目: {len(ref_items)}条", len(ref_items) >= 3)

if ref_items:
    r1 = ref_items[0]
    check("参考文献条目: 10.5pt", r1.font.font_size == 10.5, "10.5pt", f"{r1.font.font_size}pt")
    check("参考文献条目: 宋体", r1.font.font_name_east_asia == "宋体")
    check("参考文献条目: 左缩进24pt", r1.paragraph.left_indent == 24.0)
    check("参考文献条目: 无首行缩进",
          r1.paragraph.first_line_indent is None or r1.paragraph.first_line_indent == 0)

# Style distribution
style_counts = {}
for p in v.paragraphs:
    style_counts[p.style_name] = style_counts.get(p.style_name, 0) + 1
print(f"\n  成品样式分布: {style_counts}")

print(f"\n{'=' * 70}")
print(f"  端到端测试结果: 通过={PASS} 失败={FAIL} 总计={PASS+FAIL}")
print(f"{'=' * 70}")
