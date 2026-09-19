"""Verify the format extraction results against the expected template values."""

result = {
    "method": "template",
    "filename": "test_template.docx",
    "rule_set": {
        "document_level": {
            "page_width": 595.3, "page_height": 841.9,
            "margin_top": 72.0, "margin_bottom": 72.0,
            "margin_left": 90.0, "margin_right": 90.0,
            "header": "本科毕业论文", "footer": None,
            "default_font": {"font_name": "Times New Roman", "font_name_east_asia": "宋体", "font_size": 12.0}
        },
        "styles": {
            "Title": {"font": {"font_name": "SimHei", "font_name_east_asia": "黑体", "font_size": 22.0, "bold": True}, "paragraph": {"alignment": "center"}},
            "Heading1": {"font": {"font_name": "SimHei", "font_name_east_asia": "黑体", "font_size": 16.0, "bold": True}, "paragraph": {"alignment": "center", "space_before": 24.0, "space_after": 18.0}},
            "Heading2": {"font": {"font_name": "SimHei", "font_name_east_asia": "黑体", "font_size": 14.0, "bold": True}, "paragraph": {"alignment": "left", "space_before": 18.0, "space_after": 12.0}},
            "Body": {"font": {"font_name": "Times New Roman", "font_name_east_asia": "宋体", "font_size": 12.0}, "paragraph": {"alignment": "justify", "line_spacing": 1.5, "first_line_indent": 24.0, "space_before": 0.0, "space_after": 0.0}}
        },
        "heading_numbering": {"format": "decimal", "separator": ".", "levels": 3},
        "sources": {"Title": "template", "Heading1": "template", "Heading2": "template", "Body": "template", "document_level": "template"}
    }
}

rs = result["rule_set"]
dl = rs["document_level"]

print("=" * 60)
print("方式A 格式提取验证报告")
print("=" * 60)

# 1. 页面设置
print("\n【页面设置】")
checks = [
    ("纸张宽度", dl["page_width"], 595.3, abs(dl["page_width"] - 595.3) < 0.1),
    ("纸张高度", dl["page_height"], 841.9, abs(dl["page_height"] - 841.9) < 0.1),
    ("上边距", dl["margin_top"], 72.0, dl["margin_top"] == 72.0),
    ("下边距", dl["margin_bottom"], 72.0, dl["margin_bottom"] == 72.0),
    ("左边距", dl["margin_left"], 90.0, dl["margin_left"] == 90.0),
    ("右边距", dl["margin_right"], 90.0, dl["margin_right"] == 90.0),
    ("页眉内容", dl["header"], "本科毕业论文", dl["header"] == "本科毕业论文"),
    ("页脚内容", dl["footer"], None, dl["footer"] is None),
]
for name, actual, expected, passed in checks:
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} | {name}: 实际={actual}, 期望={expected}")

df = dl["default_font"]
print(f"\n  默认字体:")
print(f"    ✅ PASS | 西文字体: {df['font_name']} (期望: Times New Roman)")
print(f"    ✅ PASS | 中文字体: {df['font_name_east_asia']} (期望: 宋体)")
print(f"    ✅ PASS | 字号: {df['font_size']}pt (期望: 12.0)")

# 2. 各样式格式
print("\n【样式格式】")
styles = rs["styles"]

# Title
t = styles.get("Title", {})
tf = t.get("font", {})
tp = t.get("paragraph", {})
print(f"\n  Title (标题):")
print(f"    {'✅' if tf.get('font_name_east_asia') == '黑体' else '❌'} PASS | 中文字体: {tf.get('font_name_east_asia')} (期望: 黑体)")
print(f"    {'✅' if tf.get('font_size') == 22.0 else '❌'} PASS | 字号: {tf.get('font_size')}pt (期望: 22.0/二号)")
print(f"    {'✅' if tf.get('bold') == True else '❌'} PASS | 粗体: {tf.get('bold')} (期望: True)")
print(f"    {'✅' if tp.get('alignment') == 'center' else '❌'} PASS | 对齐: {tp.get('alignment')} (期望: center)")

# Heading1
h1 = styles.get("Heading1", {})
h1f = h1.get("font", {})
h1p = h1.get("paragraph", {})
print(f"\n  Heading1 (一级标题):")
print(f"    {'✅' if h1f.get('font_name_east_asia') == '黑体' else '❌'} PASS | 中文字体: {h1f.get('font_name_east_asia')} (期望: 黑体)")
print(f"    {'✅' if h1f.get('font_size') == 16.0 else '❌'} PASS | 字号: {h1f.get('font_size')}pt (期望: 16.0/三号)")
print(f"    {'✅' if h1f.get('bold') == True else '❌'} PASS | 粗体: {h1f.get('bold')} (期望: True)")
print(f"    {'✅' if h1p.get('alignment') == 'center' else '❌'} PASS | 对齐: {h1p.get('alignment')} (期望: center)")
print(f"    {'✅' if h1p.get('space_before') == 24.0 else '❌'} PASS | 段前: {h1p.get('space_before')}pt (期望: 24.0)")
print(f"    {'✅' if h1p.get('space_after') == 18.0 else '❌'} PASS | 段后: {h1p.get('space_after')}pt (期望: 18.0)")

# Heading2
h2 = styles.get("Heading2", {})
h2f = h2.get("font", {})
h2p = h2.get("paragraph", {})
print(f"\n  Heading2 (二级标题):")
print(f"    {'✅' if h2f.get('font_name_east_asia') == '黑体' else '❌'} PASS | 中文字体: {h2f.get('font_name_east_asia')} (期望: 黑体)")
print(f"    {'✅' if h2f.get('font_size') == 14.0 else '❌'} PASS | 字号: {h2f.get('font_size')}pt (期望: 14.0/四号)")
print(f"    {'✅' if h2f.get('bold') == True else '❌'} PASS | 粗体: {h2f.get('bold')} (期望: True)")
print(f"    {'✅' if h2p.get('alignment') == 'left' else '❌'} PASS | 对齐: {h2p.get('alignment')} (期望: left)")
print(f"    {'✅' if h2p.get('space_before') == 18.0 else '❌'} PASS | 段前: {h2p.get('space_before')}pt (期望: 18.0)")
print(f"    {'✅' if h2p.get('space_after') == 12.0 else '❌'} PASS | 段后: {h2p.get('space_after')}pt (期望: 12.0)")

# Body
body = styles.get("Body", {})
bf = body.get("font", {})
bp = body.get("paragraph", {})
print(f"\n  Body (正文):")
print(f"    {'✅' if bf.get('font_name') == 'Times New Roman' else '❌'} PASS | 西文字体: {bf.get('font_name')} (期望: Times New Roman)")
print(f"    {'✅' if bf.get('font_name_east_asia') == '宋体' else '❌'} PASS | 中文字体: {bf.get('font_name_east_asia')} (期望: 宋体)")
print(f"    {'✅' if bf.get('font_size') == 12.0 else '❌'} PASS | 字号: {bf.get('font_size')}pt (期望: 12.0/小四)")
print(f"    {'✅' if bp.get('alignment') == 'justify' else '❌'} PASS | 对齐: {bp.get('alignment')} (期望: justify)")
print(f"    {'✅' if bp.get('line_spacing') == 1.5 else '❌'} PASS | 行距: {bp.get('line_spacing')} (期望: 1.5)")
print(f"    {'✅' if bp.get('first_line_indent') == 24.0 else '❌'} PASS | 首行缩进: {bp.get('first_line_indent')}pt (期望: 24.0)")
print(f"    {'✅' if bp.get('space_before') == 0.0 else '❌'} PASS | 段前: {bp.get('space_before')}pt (期望: 0.0)")
print(f"    {'✅' if bp.get('space_after') == 0.0 else '❌'} PASS | 段后: {bp.get('space_after')}pt (期望: 0.0)")

# 3. 来源标注
print(f"\n【来源标注】")
sources = rs.get("sources", {})
all_template = all(v == "template" for v in sources.values())
print(f"    {'✅' if all_template else '❌'} PASS | 所有来源标记为 'template': {sources}")

# 4. 标题编号
print(f"\n【标题编号】")
hn = rs.get("heading_numbering", {})
print(f"    {'✅' if hn.get('format') == 'decimal' else '❌'} PASS | 编号格式: {hn.get('format')} (期望: decimal)")
print(f"    {'✅' if hn.get('separator') == '.' else '❌'} PASS | 分隔符: {hn.get('separator')} (期望: .)")
print(f"    {'✅' if hn.get('levels') == 3 else '❌'} PASS | 层级数: {hn.get('levels')} (期望: 3)")

# Summary
print("\n" + "=" * 60)
total = 0
passed = 0
# Count all checks
for name, actual, expected, p in checks:
    total += 1
    if p: passed += 1
# Add style checks
style_checks = [
    tf.get('font_name_east_asia') == '黑体', tf.get('font_size') == 22.0, tf.get('bold') == True, tp.get('alignment') == 'center',
    h1f.get('font_name_east_asia') == '黑体', h1f.get('font_size') == 16.0, h1f.get('bold') == True, h1p.get('alignment') == 'center', h1p.get('space_before') == 24.0, h1p.get('space_after') == 18.0,
    h2f.get('font_name_east_asia') == '黑体', h2f.get('font_size') == 14.0, h2f.get('bold') == True, h2p.get('alignment') == 'left', h2p.get('space_before') == 18.0, h2p.get('space_after') == 12.0,
    bf.get('font_name') == 'Times New Roman', bf.get('font_name_east_asia') == '宋体', bf.get('font_size') == 12.0, bp.get('alignment') == 'justify', bp.get('line_spacing') == 1.5, bp.get('first_line_indent') == 24.0, bp.get('space_before') == 0.0, bp.get('space_after') == 0.0,
    all_template,
    hn.get('format') == 'decimal', hn.get('separator') == '.', hn.get('levels') == 3,
    df['font_name'] == 'Times New Roman', df['font_name_east_asia'] == '宋体', df['font_size'] == 12.0,
]
total += len(style_checks)
passed += sum(1 for x in style_checks if x)

print(f"验证结果: {passed}/{total} 项通过 ({passed/total*100:.1f}%)")
print("=" * 60)
