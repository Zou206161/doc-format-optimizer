"""Verify the title detection and table font fixes."""

import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.modules.parser import parse_document
from src.modules.format_extractor import extract_format_rules
from src.modules.format_applier import apply_format
from src.modules.doc_generator import generate_document

BASE = os.path.dirname(os.path.abspath(__file__))

# Extract rules from template
tpl_doc = parse_document(os.path.join(BASE, "test_template.docx"))
rule_set = extract_format_rules(tpl_doc)

# Parse draft
draft_doc = parse_document(os.path.join(BASE, "test_draft.docx"))

# Apply format
formatted = apply_format(draft_doc, None, rule_set)

print("=" * 60)
print("修复验证测试")
print("=" * 60)

# Check style mapping
print("\n[1] 样式映射检查:")
for fp in formatted.paragraphs:
    t = fp.text[:40] + "..." if len(fp.text) > 40 else fp.text
    tag = ""
    if fp.style_key == "Title":
        tag = " ← 标题检测"
    elif fp.style_key.startswith("Heading"):
        tag = " ← 标题"
    print(f"  {fp.style_key:10s} | {t}{tag}")

# Generate document
output = os.path.join(BASE, "test_fixed_output.docx")
generate_document(formatted, output)
print(f"\n[2] 文档生成: {os.path.getsize(output)} bytes")

# Verify output
v = parse_document(output)
print(f"\n[3] 成品文档验证:")
print(f"  页面: {v.page_width}x{v.page_height}pt, 页边距 T/B/L/R={v.margin_top}/{v.margin_bottom}/{v.margin_left}/{v.margin_right}")
print(f"  页眉: '{v.header}'")

# Find title paragraph (first non-empty with Title format)
title_para = None
for p in v.paragraphs:
    if p.text.strip() and p.font.font_name_east_asia == "黑体" and p.font.font_size == 22.0:
        title_para = p
        break

print(f"\n[4] 标题段落验证:")
if title_para:
    print(f"  文本: '{title_para.text}'")
    print(f"  中文字体: {title_para.font.font_name_east_asia} (期望: 黑体) {'✅' if title_para.font.font_name_east_asia == '黑体' else '❌'}")
    print(f"  西文字体: {title_para.font.font_name} (期望: SimHei) {'✅' if title_para.font.font_name == 'SimHei' else '❌'}")
    print(f"  字号: {title_para.font.font_size}pt (期望: 22.0) {'✅' if title_para.font.font_size == 22.0 else '❌'}")
    print(f"  粗体: {title_para.font.bold} (期望: True) {'✅' if title_para.font.bold == True else '❌'}")
    print(f"  对齐: {title_para.paragraph.alignment} (期望: center) {'✅' if title_para.paragraph.alignment == 'center' else '❌'}")
else:
    print("  ❌ 未找到标题段落!")

# Check all paragraphs
print(f"\n[5] 全部段落:")
for p in v.paragraphs:
    east = p.font.font_name_east_asia or "?"
    name = p.font.font_name or "?"
    sz = p.font.font_size or "?"
    bold = p.font.bold
    a = p.paragraph.alignment or "?"
    ls = p.paragraph.line_spacing or "?"
    ind = p.paragraph.first_line_indent or "?"
    t = p.text[:35] + "..." if len(p.text) > 35 else p.text
    print(f"  {east}/{name} {sz}pt bold={bold} a={a} ls={ls} ind={ind} | {t}")

# Check table
print(f"\n[6] 表格验证:")
if v.tables:
    t = v.tables[0]
    print(f"  行列: {t.rows}x{t.cols}")
    for i, row in enumerate(t.cells):
        print(f"  Row {i}: {row}")

# Summary
print(f"\n{'=' * 60}")
title_ok = title_para and title_para.font.font_name_east_asia == "黑体" and title_para.font.font_size == 22.0 and title_para.font.bold == True and title_para.paragraph.alignment == "center"
table_ok = v.tables and v.tables[0].cells[0][1] == "应用领域"
print(f"标题格式: {'✅ PASS' if title_ok else '❌ FAIL'}")
print(f"表格文字: {'✅ PASS' if table_ok else '❌ FAIL'} (应用领域 not garbled)")
print(f"{'=' * 60}")
