"""Test preset-only API endpoints."""
import requests, json

API = "http://localhost:8000/api"

print("=" * 60)
print("  预设模板单独使用测试")
print("=" * 60)

PASS = 0
FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  ✅ {name}")
        PASS += 1
    else:
        print(f"  ❌ {name} — {detail}")
        FAIL += 1

# Test 1: /from-preset endpoint (preset only, no text)
print("\n【1】 /api/rules/from-preset (单独使用预设模板)")
r = requests.post(f"{API}/rules/from-preset", data={"preset_id": "undergraduate_thesis"})
print(f"  状态码: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"  method: {data.get('method')}")
    print(f"  preset_name: {data.get('preset_name')}")
    styles = list(data["rule_set"]["styles"].keys())
    print(f"  styles: {styles}")
    check("返回200", r.status_code == 200)
    check("method=preset", data.get("method") == "preset")
    check("包含Title样式", "Title" in styles)
    check("包含Body样式", "Body" in styles)
    check("包含Reference样式", "Reference" in styles)
else:
    check("返回200", False, r.text[:100])

# Test 2: /from-text with empty text but preset_id
print("\n【2】 /api/rules/from-text (空文字 + 预设模板)")
r = requests.post(f"{API}/rules/from-text", data={"text": "", "preset_id": "master_thesis"})
print(f"  状态码: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"  method: {data.get('method')}")
    styles = list(data["rule_set"]["styles"].keys())
    print(f"  styles: {styles}")
    check("返回200", r.status_code == 200)
    check("method=preset", data.get("method") == "preset")
    check("包含Heading1样式", "Heading1" in styles)
else:
    check("返回200", False, r.text[:100])

# Test 3: /from-text with no text and no preset (should error)
print("\n【3】 /api/rules/from-text (无文字、无预设 → 应报错)")
r = requests.post(f"{API}/rules/from-text", data={"text": ""})
print(f"  状态码: {r.status_code}")
print(f"  响应: {r.text[:100]}")
check("返回400(参数错误)", r.status_code == 400)

# Test 4: /from-text with text + preset (merge)
print("\n【4】 /api/rules/from-text (文字+预设 → 合并)")
r = requests.post(f"{API}/rules/from-text", data={
    "text": "正文用小四号宋体，1.5倍行距",
    "preset_id": "undergraduate_thesis",
})
print(f"  状态码: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"  method: {data.get('method')}")
    check("返回200", r.status_code == 200)
    check("method=text_parse", data.get("method") == "text_parse")
else:
    check("返回200", False, r.text[:100])

print(f"\n{'=' * 60}")
print(f"  测试结果: 通过={PASS} 失败={FAIL} 总计={PASS+FAIL}")
print(f"{'=' * 60}")
