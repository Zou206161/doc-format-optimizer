"""Test API endpoints end-to-end via HTTP requests."""

import json
import os
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def test_health():
    """Test health check."""
    print("[Test] GET /api/health")
    with urllib.request.urlopen(f"{BASE_URL}/api/health") as resp:
        data = json.loads(resp.read())
        assert data["status"] == "ok"
        print(f"  ✅ Response: {data}")
    print()


def test_presets():
    """Test presets list."""
    print("[Test] GET /api/rules/presets")
    with urllib.request.urlopen(f"{BASE_URL}/api/rules/presets") as resp:
        data = json.loads(resp.read())
        assert len(data["presets"]) == 3
        print(f"  ✅ Presets: {len(data['presets'])} items")
        for p in data["presets"]:
            print(f"     - {p['id']}: {p['name']}")
    print()


def test_from_template():
    """Test Method A: format extraction from template."""
    print("[Test] POST /api/rules/from-template")
    template_path = os.path.join(BASE_DIR, "test_template.docx")

    # Build multipart form data
    boundary = "----TestBoundary1234567890"
    with open(template_path, "rb") as f:
        file_content = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="test_template.docx"\r\n'
        f"Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document\r\n\r\n"
    ).encode() + file_content + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{BASE_URL}/api/rules/from-template",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        assert data["method"] == "template"
        assert "rule_set" in data
        rs = data["rule_set"]
        print(f"  ✅ Method: {data['method']}")
        print(f"  ✅ Filename: {data['filename']}")
        print(f"  ✅ Styles: {', '.join(rs['styles'].keys())}")
        print(f"  ✅ Page: {rs['document_level']['page_width']} x {rs['document_level']['page_height']} pt")
        print(f"  ✅ Margins: T={rs['document_level']['margin_top']} B={rs['document_level']['margin_bottom']} L={rs['document_level']['margin_left']} R={rs['document_level']['margin_right']}")
        print(f"  ✅ Header: '{rs['document_level']['header']}'")
        for name, style in rs["styles"].items():
            f_data = style["font"]
            p_data = style["paragraph"]
            print(f"  ✅ {name}: {f_data.get('font_name_east_asia','?')}/{f_data.get('font_name','?')} {f_data.get('font_size','?')}pt bold={f_data.get('bold')} | align={p_data.get('alignment')} ls={p_data.get('line_spacing')} indent={p_data.get('first_line_indent')}")

        # Save rules for next test
        rules_path = os.path.join(BASE_DIR, "test_api_rules.json")
        with open(rules_path, "w", encoding="utf-8") as f:
            json.dump(rs, f, ensure_ascii=False)
        print(f"  ✅ Rules saved for next test")
    print()
    return rs


def test_from_template_error():
    """Test error handling: non-.docx file."""
    print("[Test] POST /api/rules/from-template (non-docx file)")
    boundary = "----TestBoundary1234567890"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
        f"Content-Type: text/plain\r\n\r\n"
        f"hello world\r\n"
        f"--{boundary}--\r\n"
    ).encode()

    req = urllib.request.Request(
        f"{BASE_URL}/api/rules/from-template",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req)
        print("  ❌ Should have returned error")
    except urllib.error.HTTPError as e:
        data = json.loads(e.read())
        assert "error" in data
        assert "Only .docx" in data["error"]
        print(f"  ✅ Error handling correct: {data['error']} (HTTP {e.code})")
    print()


def test_optimize_preview():
    """Test optimization preview endpoint."""
    print("[Test] POST /api/optimize/preview")
    draft_path = os.path.join(BASE_DIR, "test_draft.docx")

    boundary = "----TestBoundary1234567890"
    with open(draft_path, "rb") as f:
        file_content = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="test_draft.docx"\r\n'
        f"Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document\r\n\r\n"
    ).encode() + file_content + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{BASE_URL}/api/optimize/preview",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        print(f"  ✅ Total paragraphs: {len(data.get('paragraphs', []))}")
        print(f"  ✅ Total changes: {data.get('total_changes', 0)}")
        print(f"  ✅ By type: {data.get('by_type', {})}")
        print(f"  ℹ️  (LLM not configured — all paragraphs preserved as original)")
        for p in data.get("paragraphs", [])[:3]:
            print(f"     para {p['index']}: changes={len(p.get('changes', []))}, text={p['optimized_text'][:40]}...")
    print()


def test_optimize_generate(rules_json):
    """Test full document generation endpoint."""
    print("[Test] POST /api/optimize/generate")
    draft_path = os.path.join(BASE_DIR, "test_draft.docx")
    output_path = os.path.join(BASE_DIR, "test_api_成品.docx")

    boundary = "----TestBoundary1234567890"
    with open(draft_path, "rb") as f:
        file_content = f.read()

    rules_str = json.dumps(rules_json, ensure_ascii=False)

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="test_draft.docx"\r\n'
        f"Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document\r\n\r\n"
    ).encode() + file_content + (
        f"\r\n--{boundary}\r\n"
        f'Content-Disposition: form-data; name="rules_json"\r\n\r\n'
        f"{rules_str}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="skip_optimization"\r\n\r\n'
        f"true\r\n"
        f"--{boundary}--\r\n"
    ).encode()

    req = urllib.request.Request(
        f"{BASE_URL}/api/optimize/generate",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        content_type = resp.headers.get("Content-Type", "")
        content_disp = resp.headers.get("Content-Disposition", "")
        file_data = resp.read()

        with open(output_path, "wb") as f:
            f.write(file_data)

        file_size = len(file_data)
        print(f"  ✅ Content-Type: {content_type}")
        print(f"  ✅ Content-Disposition: {content_disp}")
        print(f"  ✅ File saved: {output_path} ({file_size} bytes / {file_size/1024:.1f} KB)")

    # Verify the generated document
    print(f"\n  Verifying generated document...")
    import sys
    sys.path.insert(0, BASE_DIR)
    from src.modules.parser import parse_document
    verify = parse_document(output_path)
    print(f"  ✅ Paragraphs: {len(verify.paragraphs)}")
    print(f"  ✅ Tables: {len(verify.tables)}")
    print(f"  ✅ Page: {verify.page_width} x {verify.page_height} pt")
    print(f"  ✅ Margins: T={verify.margin_top} B={verify.margin_bottom} L={verify.margin_left} R={verify.margin_right}")
    print(f"  ✅ Header: '{verify.header}'")
    for p in verify.paragraphs:
        east = p.font.font_name_east_asia or "?"
        size = p.font.font_size or "?"
        align = p.paragraph.alignment or "?"
        ls = p.paragraph.line_spacing or "?"
        indent = p.paragraph.first_line_indent or "?"
        text_preview = p.text[:35] + "..." if len(p.text) > 35 else p.text
        print(f"     [{p.style_name}] {east} {size}pt align={align} ls={ls} indent={indent} | {text_preview}")
    print()


def test_optimize_generate_error():
    """Test error handling: invalid rules JSON."""
    print("[Test] POST /api/optimize/generate (invalid rules_json)")
    boundary = "----TestBoundary1234567890"
    draft_path = os.path.join(BASE_DIR, "test_draft.docx")
    with open(draft_path, "rb") as f:
        file_content = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="test_draft.docx"\r\n'
        f"Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document\r\n\r\n"
    ).encode() + file_content + (
        f"\r\n--{boundary}\r\n"
        f'Content-Disposition: form-data; name="rules_json"\r\n\r\n'
        f'{"invalid": "json"}\r\n'
        f"--{boundary}--\r\n"
    ).encode()

    req = urllib.request.Request(
        f"{BASE_URL}/api/optimize/generate",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req)
        print("  ❌ Should have returned error")
    except urllib.error.HTTPError as e:
        data = json.loads(e.read())
        print(f"  ✅ Error handling correct: HTTP {e.code} - {data.get('error', '')[:80]}")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("方式A 端到端 API 验证测试")
    print("=" * 60)
    print()

    test_health()
    test_presets()
    test_from_template_error()
    rules = test_from_template()
    test_optimize_preview()
    test_optimize_generate(rules)
    test_optimize_generate_error()

    print("=" * 60)
    print("全部 API 测试完成!")
    print("=" * 60)
