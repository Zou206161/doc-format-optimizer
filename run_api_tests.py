import json, os, sys, urllib.request, urllib.error

BASE_URL = 'http://localhost:8000'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
boundary = '----TestBoundary123'

def multipart(fields_and_files):
    parts = []
    for name, (filename, content, content_type) in fields_and_files.items():
        parts.append(f'--{boundary}\r\n'.encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"'.encode())
        if filename:
            parts.append(f'; filename="{filename}"'.encode())
        parts.append(b'\r\n')
        if content_type:
            parts.append(f'Content-Type: {content_type}\r\n'.encode())
        parts.append(b'\r\n')
        if isinstance(content, str):
            parts.append(content.encode('utf-8'))
        else:
            parts.append(content)
        parts.append(b'\r\n')
    parts.append(f'--{boundary}--\r\n'.encode())
    return b''.join(parts)

# Test 1: Health
print('[Test 1] GET /api/health')
with urllib.request.urlopen(f'{BASE_URL}/api/health') as resp:
    print(f'  PASS: {json.loads(resp.read())}')

# Test 2: Presets
print('\n[Test 2] GET /api/rules/presets')
with urllib.request.urlopen(f'{BASE_URL}/api/rules/presets') as resp:
    data = json.loads(resp.read())
    print(f'  PASS: {len(data["presets"])} presets')

# Test 3: Non-docx error
print('\n[Test 3] POST /api/rules/from-template (non-docx)')
body = multipart({'file': ('test.txt', b'hello world', 'text/plain')})
req = urllib.request.Request(f'{BASE_URL}/api/rules/from-template', data=body, headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}, method='POST')
try:
    urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    print(f'  PASS: HTTP {e.code} - {json.loads(e.read())["error"]}')

# Test 4: Template extraction
print('\n[Test 4] POST /api/rules/from-template')
with open(os.path.join(BASE_DIR, 'test_template.docx'), 'rb') as f:
    tpl = f.read()
body = multipart({'file': ('test_template.docx', tpl, 'application/octet-stream')})
req = urllib.request.Request(f'{BASE_URL}/api/rules/from-template', data=body, headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}, method='POST')
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    rs = data['rule_set']
    dl = rs['document_level']
    print(f'  PASS: styles={list(rs["styles"].keys())}')
    print(f'  Page: {dl["page_width"]}x{dl["page_height"]}pt, margins T/B/L/R={dl["margin_top"]}/{dl["margin_bottom"]}/{dl["margin_left"]}/{dl["margin_right"]}')
    print(f'  Header: {dl["header"]}')
    for n, s in rs['styles'].items():
        fd = s['font']; pd = s['paragraph']
        print(f'  {n}: {fd.get("font_name_east_asia","?")}/{fd.get("font_name","?")} {fd.get("font_size","?")}pt bold={fd.get("bold")} align={pd.get("alignment")} ls={pd.get("line_spacing")} indent={pd.get("first_line_indent")}')

# Test 5: Optimization preview
print('\n[Test 5] POST /api/optimize/preview')
with open(os.path.join(BASE_DIR, 'test_draft.docx'), 'rb') as f:
    draft = f.read()
body = multipart({'file': ('test_draft.docx', draft, 'application/octet-stream')})
req = urllib.request.Request(f'{BASE_URL}/api/optimize/preview', data=body, headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}, method='POST')
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    print(f'  PASS: paragraphs={len(data["paragraphs"])}, changes={data["total_changes"]} (LLM not configured)')

# Test 6: Document generation
print('\n[Test 6] POST /api/optimize/generate')
out_path = os.path.join(BASE_DIR, 'test_api_output.docx')
rules_str = json.dumps(rs, ensure_ascii=False)
body = multipart({
    'file': ('test_draft.docx', draft, 'application/octet-stream'),
    'rules_json': (None, rules_str, None),
    'skip_optimization': (None, 'true', None),
})
req = urllib.request.Request(f'{BASE_URL}/api/optimize/generate', data=body, headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}, method='POST')
with urllib.request.urlopen(req) as resp:
    file_data = resp.read()
    with open(out_path, 'wb') as f:
        f.write(file_data)
    print(f'  PASS: {len(file_data)} bytes ({len(file_data)/1024:.1f} KB)')
    print(f'  Content-Type: {resp.headers.get("Content-Type","")}')
    print(f'  Content-Disposition: {resp.headers.get("Content-Disposition","")}')

# Verify output
sys.path.insert(0, BASE_DIR)
from src.modules.parser import parse_document
v = parse_document(out_path)
print(f'  Verify: {len(v.paragraphs)} paras, {len(v.tables)} tables')
print(f'  Page: {v.page_width}x{v.page_height}pt, margins={v.margin_top}/{v.margin_bottom}/{v.margin_left}/{v.margin_right}')
print(f'  Header: {v.header}')
for p in v.paragraphs:
    e = p.font.font_name_east_asia or '?'
    sz = p.font.font_size or '?'
    a = p.paragraph.alignment or '?'
    ls = p.paragraph.line_spacing or '?'
    ind = p.paragraph.first_line_indent or '?'
    t = p.text[:35] + '...' if len(p.text) > 35 else p.text
    print(f'    [{p.style_name}] {e} {sz}pt a={a} ls={ls} ind={ind} | {t}')

# Test 7: Invalid rules JSON
print('\n[Test 7] POST /api/optimize/generate (invalid rules_json)')
body = multipart({
    'file': ('test_draft.docx', draft, 'application/octet-stream'),
    'rules_json': (None, '{"invalid":true}', None),
})
req = urllib.request.Request(f'{BASE_URL}/api/optimize/generate', data=body, headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}, method='POST')
try:
    urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    print(f'  PASS: HTTP {e.code} - {json.loads(e.read()).get("error","")[:60]}')

print('\n' + '='*60)
print('All API tests completed!')
print('='*60)
