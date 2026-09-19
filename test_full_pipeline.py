"""End-to-end test: template extraction -> format application -> document generation."""

import json
import os
import sys
import tempfile

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.modules.parser import parse_document
from src.modules.format_extractor import extract_format_rules
from src.modules.format_applier import apply_format
from src.modules.doc_generator import generate_document

BASE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(BASE, "test_template.docx")
DRAFT = os.path.join(BASE, "test_draft.docx")

print("=" * 60)
print("方式A 端到端管线测试")
print("=" * 60)

# Step 1: Parse template and extract rules
print("\n[Step 1] 解析模板文档并提取格式规则...")
template_doc = parse_document(TEMPLATE)
rule_set = extract_format_rules(template_doc)
print(f"  模板段落数: {len(template_doc.paragraphs)}")
print(f"  模板表格数: {len(template_doc.tables)}")
print(f"  提取样式数: {len(rule_set.styles)} ({', '.join(rule_set.styles.keys())})")
print(f"  页面尺寸: {rule_set.document_level.page_width} x {rule_set.document_level.page_height} pt")
print(f"  页边距: 上{rule_set.document_level.margin_top} 下{rule_set.document_level.margin_bottom} 左{rule_set.document_level.margin_left} 右{rule_set.document_level.margin_right}")

# Save rules.json
rules_path = os.path.join(BASE, "test_rules.json")
with open(rules_path, "w", encoding="utf-8") as f:
    json.dump(json.loads(rule_set.model_dump_json()), f, ensure_ascii=False, indent=2)
print(f"  rules.json 已保存: {rules_path}")

# Step 2: Parse draft document
print(f"\n[Step 2] 解析草稿文档...")
draft_doc = parse_document(DRAFT)
print(f"  草稿段落数: {len(draft_doc.paragraphs)}")
print(f"  草稿表格数: {len(draft_doc.tables)}")
for p in draft_doc.paragraphs:
    style_tag = f"[{p.style_name}]" if p.is_heading else "[Normal]"
    text_preview = p.text[:50] + "..." if len(p.text) > 50 else p.text
    print(f"    段落 {p.index}: {style_tag} {text_preview}")

# Step 3: Apply format (skip optimization since no LLM)
print(f"\n[Step 3] 套用格式规则（跳过LLM优化）...")
formatted = apply_format(draft_doc, None, rule_set)
print(f"  格式化段落数: {len(formatted.paragraphs)}")
print(f"  格式化表格数: {len(formatted.tables)}")
for fp in formatted.paragraphs:
    print(f"    style_key={fp.style_key}, heading={fp.is_heading}(L{fp.heading_level}), text={fp.text[:40]}...")

# Step 4: Generate document
print(f"\n[Step 4] 生成成品文档...")
output_path = os.path.join(BASE, "test_output_成品.docx")
generate_document(formatted, output_path)
file_size = os.path.getsize(output_path)
print(f"  成品文档已生成: {output_path}")
print(f"  文件大小: {file_size} bytes ({file_size/1024:.1f} KB)")

# Step 5: Verify the generated document
print(f"\n[Step 5] 验证成品文档...")
verify_doc = parse_document(output_path)
print(f"  成品段落数: {len(verify_doc.paragraphs)} (原草稿: {len(draft_doc.paragraphs)})")
print(f"  成品表格数: {len(verify_doc.tables)} (原草稿: {len(draft_doc.tables)})")

# Check page setup
print(f"\n  页面设置验证:")
print(f"    纸张: {verify_doc.page_width} x {verify_doc.page_height} pt (期望: 595.3 x 841.9)")
margin_ok = (
    verify_doc.margin_top == 72.0 and
    verify_doc.margin_bottom == 72.0 and
    verify_doc.margin_left == 90.0 and
    verify_doc.margin_right == 90.0
)
print(f"    页边距: 上{verify_doc.margin_top} 下{verify_doc.margin_bottom} 左{verify_doc.margin_left} 右{verify_doc.margin_right} {'✅' if margin_ok else '❌'}")
print(f"    页眉: '{verify_doc.header}' {'✅' if verify_doc.header == '本科毕业论文' else '❌'}")

# Check paragraphs
print(f"\n  段落格式验证:")
for p in verify_doc.paragraphs:
    text_preview = p.text[:40] + "..." if len(p.text) > 40 else p.text
    font_name = p.font.font_name or "?"
    east = p.font.font_name_east_asia or "?"
    size = p.font.font_size or "?"
    align = p.paragraph.alignment or "?"
    ls = p.paragraph.line_spacing or "?"
    indent = p.paragraph.first_line_indent or "?"
    print(f"    段落{p.index} [{p.style_name}]: font={east}/{font_name}/{size}pt, align={align}, ls={ls}, indent={indent}")
    print(f"             text: {text_preview}")

# Check table
if verify_doc.tables:
    t = verify_doc.tables[0]
    print(f"\n  表格验证:")
    print(f"    行列: {t.rows}x{t.cols}")
    for i, row in enumerate(t.cells):
        print(f"    Row {i}: {row}")

print("\n" + "=" * 60)
print("端到端管线测试完成!")
print("=" * 60)
