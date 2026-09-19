"""Generate the final document via API for user to download."""

import json
import os
import urllib.request

BASE_URL = "http://localhost:8000"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOUNDARY = "----FinalGen"

def multipart(fields):
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
    return b"".join(parts)

import time
time.sleep(5)

# Step 1: Extract rules from template
print("提取格式规则...")
with open(os.path.join(BASE_DIR, "test_template.docx"), "rb") as f:
    tpl = f.read()
body = multipart({"file": ("template.docx", tpl, "application/octet-stream")})
req = urllib.request.Request(f"{BASE_URL}/api/rules/from-template", data=body,
    headers={"Content-Type": f"multipart/form-data; boundary={BOUNDARY}"}, method="POST")
with urllib.request.urlopen(req) as resp:
    rules = json.loads(resp.read())["rule_set"]
    print(f"  样式: {list(rules['styles'].keys())}")

# Step 2: Generate document
print("生成成品文档...")
with open(os.path.join(BASE_DIR, "test_draft.docx"), "rb") as f:
    draft = f.read()
rules_str = json.dumps(rules, ensure_ascii=False)
body = multipart({
    "file": ("draft.docx", draft, "application/octet-stream"),
    "rules_json": rules_str,
    "skip_optimization": "true",
})
req = urllib.request.Request(f"{BASE_URL}/api/optimize/generate", data=body,
    headers={"Content-Type": f"multipart/form-data; boundary={BOUNDARY}"}, method="POST")
with urllib.request.urlopen(req) as resp:
    data = resp.read()
    out_path = os.path.join(BASE_DIR, "成品_修复后.docx")
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"  文件: {out_path} ({len(data)} bytes)")
    print(f"  Content-Disposition: {resp.headers.get('Content-Disposition', '')}")

print("\n完成！请打开文件查看格式。")
