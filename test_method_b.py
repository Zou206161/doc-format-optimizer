"""Test Method B: text requirement parsing via API and full pipeline."""

import json
import os
import sys
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOUNDARY = "----TestBoundary123"


def post_form(endpoint, fields, expect_binary=False):
    """Submit multipart form data. Returns (status_code, json_or_bytes)."""
    parts = []
    for name, value in fields.items():
        if isinstance(value, tuple):
            filename, content, content_type = value
            parts.append(f"--{BOUNDARY}\r\n".encode())
            parts.append(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode())
            if content_type:
                parts.append(f"Content-Type: {content_type}\r\n".encode())
            parts.append(b"\r\n")
            parts.append(content if isinstance(content, bytes) else content.encode("utf-8"))
            parts.append(b"\r\n")
        else:
            parts.append(f"--{BOUNDARY}\r\n".encode())
            parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
            parts.append(value.encode("utf-8") if isinstance(value, str) else value)
            parts.append(b"\r\n")
    parts.append(f"--{BOUNDARY}--\r\n".encode())
    body = b"".join(parts)

    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={BOUNDARY}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            if expect_binary:
                return resp.status, raw
            return resp.status, json.loads(raw)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw


def print_rule_set(rs, indent="  "):
    """Pretty print a FormatRuleSet."""
    dl = rs["document_level"]
    print(f"{indent}页面: {dl['page_width']}x{dl['page_height']}pt, 页边距 T/B/L/R={dl['margin_top']}/{dl['margin_bottom']}/{dl['margin_left']}/{dl['margin_right']}")
    print(f"{indent}页眉: {dl.get('header')}, 页脚: {dl.get('footer')}")
    df = dl["default_font"]
    print(f"{indent}默认字体: {df.get('font_name_east_asia','?')}/{df.get('font_name','?')} {df.get('font_size','?')}pt")
    for name, style in rs["styles"].items():
        f = style["font"]
        p = style["paragraph"]
        print(f"{indent}{name}: {f.get('font_name_east_asia','?')}/{f.get('font_name','?')} {f.get('font_size','?')}pt bold={f.get('bold')} align={p.get('alignment')} ls={p.get('line_spacing')} indent={p.get('first_line_indent')} space_b={p.get('space_before')} space_a={p.get('space_after')}")
    sources = rs.get("sources", {})
    if sources:
        # Count by source type
        counts = {}
        for v in sources.values():
            counts[v] = counts.get(v, 0) + 1
        print(f"{indent}来源标注: {counts} (共{len(sources)}项)")
    else:
        print(f"{indent}来源标注: (空)")


# ============================================================
# Test 1: Text with preset keywords (undergraduate)
# ============================================================
print("=" * 60)
print("[Test 1] 文字解析 — 含'本科'关键词（应匹配本科预设模板）")
print("=" * 60)
text1 = "本科毕业论文格式要求：一级标题黑体三号居中，二级标题黑体四号，正文宋体小四1.5倍行距首行缩进2字符"
status, data = post_form("/api/rules/from-text", {"text": text1})
print(f"  HTTP {status}")
assert status == 200, f"Expected 200, got {status}"
rs1 = data["rule_set"]
print(f"  method: {data['method']}")
print_rule_set(rs1)

sources = rs1.get("sources", {})
has_preset = any(v == "preset" for v in sources.values())
has_default = any(v == "default" for v in sources.values())
print(f"\n  验证:")
print(f"    {'✅' if has_preset else '❌'} 来源含 'preset' 标记 (预设模板被使用)")
print(f"    {'✅' if has_default else '❌'} 来源含 'default' 标记 (学术默认值填充)")
body = rs1["styles"].get("Body", {})
bf = body.get("font", {})
bp = body.get("paragraph", {})
print(f"    {'✅' if bf.get('font_name_east_asia') == '宋体' else '❌'} 正文中文字体: {bf.get('font_name_east_asia')} (期望: 宋体)")
print(f"    {'✅' if bf.get('font_size') == 12.0 else '❌'} 正文字号: {bf.get('font_size')}pt (期望: 12.0/小四)")
print(f"    {'✅' if bp.get('line_spacing') == 1.5 else '❌'} 正文行距: {bp.get('line_spacing')} (期望: 1.5)")
print(f"    {'✅' if bp.get('first_line_indent') == 24.0 else '❌'} 首行缩进: {bp.get('first_line_indent')}pt (期望: 24.0)")
h1 = rs1["styles"].get("Heading1", {})
h1f = h1.get("font", {})
print(f"    {'✅' if h1f.get('font_name_east_asia') == '黑体' else '❌'} 一级标题字体: {h1f.get('font_name_east_asia')} (期望: 黑体)")
print(f"    {'✅' if h1f.get('font_size') == 16.0 else '❌'} 一级标题字号: {h1f.get('font_size')}pt (期望: 16.0/三号)")
dl = rs1["document_level"]
print(f"    {'✅' if dl.get('page_width') == 595.3 else '❌'} 纸张宽度: {dl.get('page_width')} (期望: 595.3/A4)")
print()

# ============================================================
# Test 2: Text with master thesis keywords
# ============================================================
print("=" * 60)
print("[Test 2] 文字解析 — 含'硕士'关键词（应匹配硕士预设模板）")
print("=" * 60)
text2 = "硕士学位论文格式：标题黑体小二号，正文宋体小四号1.5倍行距"
status, data = post_form("/api/rules/from-text", {"text": text2})
print(f"  HTTP {status}")
assert status == 200
rs2 = data["rule_set"]
print(f"  method: {data['method']}")
print_rule_set(rs2)

sources2 = rs2.get("sources", {})
has_preset2 = any(v == "preset" for v in sources2.values())
print(f"\n  验证:")
print(f"    {'✅' if has_preset2 else '❌'} 来源含 'preset' 标记")
h1_2 = rs2["styles"].get("Heading1", {})
h1f_2 = h1_2.get("font", {})
print(f"    {'✅' if h1f_2.get('font_size') == 18.0 else '❌'} 一级标题字号: {h1f_2.get('font_size')}pt (期望: 18.0/小二, 硕士模板)")
print()

# ============================================================
# Test 3: Text with explicit preset_id (journal)
# ============================================================
print("=" * 60)
print("[Test 3] 文字解析 — 显式指定 preset_id=journal_article")
print("=" * 60)
text3 = "期刊投稿格式要求：正文五号字"
status, data = post_form("/api/rules/from-text", {"text": text3, "preset_id": "journal_article"})
print(f"  HTTP {status}")
assert status == 200
rs3 = data["rule_set"]
print(f"  method: {data['method']}")
print_rule_set(rs3)

body3 = rs3["styles"].get("Body", {})
bf3 = body3.get("font", {})
dl3 = rs3["document_level"]
sources3 = rs3.get("sources", {})
has_preset3 = any(v == "preset" for v in sources3.values())
print(f"\n  验证:")
print(f"    {'✅' if bf3.get('font_size') == 10.5 else '❌'} 正文字号: {bf3.get('font_size')}pt (期望: 10.5/五号, 期刊模板)")
print(f"    {'✅' if dl3.get('margin_top') == 54.0 else '❌'} 上边距: {dl3.get('margin_top')}pt (期望: 54.0, 期刊模板)")
print(f"    {'✅' if has_preset3 else '❌'} 来源含 'preset' 标记")
print()

# ============================================================
# Test 4: Text without preset keywords (academic defaults only)
# ============================================================
print("=" * 60)
print("[Test 4] 文字解析 — 无预设关键词（仅学术默认值）")
print("=" * 60)
text4 = "文档标题居中，正文两端对齐"
status, data = post_form("/api/rules/from-text", {"text": text4})
print(f"  HTTP {status}")
assert status == 200
rs4 = data["rule_set"]
print(f"  method: {data['method']}")
print_rule_set(rs4)

sources4 = rs4.get("sources", {})
all_default = len(sources4) > 0 and all(v == "default" for v in sources4.values())
has_preset4 = any(v == "preset" for v in sources4.values())
print(f"\n  验证:")
print(f"    {'✅' if not has_preset4 else '❌'} 无 'preset' 标记 (未匹配预设)")
print(f"    {'✅' if all_default else '❌'} 所有来源标记为 'default' (共{len(sources4)}项)")
body4 = rs4["styles"].get("Body", {})
bf4 = body4.get("font", {})
bp4 = body4.get("paragraph", {})
print(f"    {'✅' if bf4.get('font_name_east_asia') == '宋体' else '❌'} 默认中文字体: {bf4.get('font_name_east_asia')} (期望: 宋体)")
print(f"    {'✅' if bf4.get('font_size') == 12.0 else '❌'} 默认字号: {bf4.get('font_size')}pt (期望: 12.0/小四)")
print(f"    {'✅' if bp4.get('line_spacing') == 1.5 else '❌'} 默认行距: {bp4.get('line_spacing')} (期望: 1.5)")
print(f"    {'✅' if bp4.get('first_line_indent') == 24.0 else '❌'} 默认首行缩进: {bp4.get('first_line_indent')}pt (期望: 24.0)")
print()

# ============================================================
# Test 5: Full pipeline — text parse → generate document
# ============================================================
print("=" * 60)
print("[Test 5] 完整管线 — 文字解析 → 草稿上传 → 文档生成")
print("=" * 60)

# Step 1: Parse text to get rules
text5 = "本科毕业论文：一级标题黑体三号居中，正文宋体小四1.5倍行距"
print(f"\n  [Step 1] 文字解析格式要求...")
print(f"  输入: '{text5}'")
status, data = post_form("/api/rules/from-text", {"text": text5})
assert status == 200
rs5 = data["rule_set"]
print(f"  ✅ 格式规则生成成功, styles: {list(rs5['styles'].keys())}")

# Step 2: Upload draft + rules → generate document
print(f"\n  [Step 2] 上传草稿 + 规则 → 生成成品文档...")
draft_path = os.path.join(BASE_DIR, "test_draft.docx")
with open(draft_path, "rb") as f:
    draft_content = f.read()

rules_json_str = json.dumps(rs5, ensure_ascii=False)
output_path = os.path.join(BASE_DIR, "test_method_b_output.docx")

status, data = post_form("/api/optimize/generate", {
    "file": ("test_draft.docx", draft_content, "application/octet-stream"),
    "rules_json": rules_json_str,
    "skip_optimization": "true",
}, expect_binary=True)

if status == 200:
    with open(output_path, "wb") as f:
        f.write(data)
    file_size = len(data)
    print(f"  ✅ 文档生成成功: {file_size} bytes ({file_size/1024:.1f} KB)")
else:
    print(f"  ❌ 文档生成失败: HTTP {status}")
    if isinstance(data, dict):
        print(f"     Error: {data.get('error', '')}")
    sys.exit(1)

# Step 3: Verify the output document
print(f"\n  [Step 3] 验证成品文档格式...")
sys.path.insert(0, BASE_DIR)
from src.modules.parser import parse_document
v = parse_document(output_path)
print(f"  段落数: {len(v.paragraphs)} (草稿原: 9)")
print(f"  表格数: {len(v.tables)} (草稿原: 1)")
print(f"  页面: {v.page_width}x{v.page_height}pt (期望: 595.3x841.9)")
print(f"  页边距: T={v.margin_top} B={v.margin_bottom} L={v.margin_left} R={v.margin_right}")
print(f"  页眉: '{v.header}'")
body_style = rs5["styles"].get("Body", {})
bf5 = body_style.get("font", {})
bp5 = body_style.get("paragraph", {})
print(f"  期望正文: {bf5.get('font_name_east_asia')}/{bf5.get('font_name')} {bf5.get('font_size')}pt align={bp5.get('alignment')} ls={bp5.get('line_spacing')} indent={bp5.get('first_line_indent')}")
h1_style = rs5["styles"].get("Heading1", {})
h1f5 = h1_style.get("font", {})
h1p5 = h1_style.get("paragraph", {})
print(f"  期望H1: {h1f5.get('font_name_east_asia')} {h1f5.get('font_size')}pt bold={h1f5.get('bold')} align={h1p5.get('alignment')}")
for p in v.paragraphs:
    east = p.font.font_name_east_asia or "?"
    sz = p.font.font_size or "?"
    a = p.paragraph.alignment or "?"
    ls = p.paragraph.line_spacing or "?"
    ind = p.paragraph.first_line_indent or "?"
    t = p.text[:35] + "..." if len(p.text) > 35 else p.text
    print(f"    [{p.style_name}] {east} {sz}pt a={a} ls={ls} ind={ind} | {t}")
print()

# ============================================================
# Test 6: Sources detail verification
# ============================================================
print("=" * 60)
print("[Test 6] 来源标注详情验证")
print("=" * 60)
# Re-use rs1 (undergraduate preset)
print(f"  Test 1 (本科预设) 来源详情:")
for key, val in sorted(sources.items()):
    print(f"    {key}: {val}")
print()

print("=" * 60)
print("方式B 端到端验证测试完成!")
print("=" * 60)
