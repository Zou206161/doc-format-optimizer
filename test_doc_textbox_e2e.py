"""端到端测试：.doc 文件 + 文本框批注解析。"""
import os, sys, requests, json

API = "http://localhost:8000/api"
BASE = os.path.dirname(os.path.abspath(__file__))

# The user's uploaded .doc file (already copied as user_uploaded.doc)
DOC_PATH = os.path.join(BASE, "user_uploaded.doc")

print("=" * 70)
print("  端到端测试：.doc 文件 + 文本框批注解析")
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

# Step 1: Upload .doc file and extract format rules
print("\n【Step 1】上传 .doc 模板文件")
print(f"  文件: {DOC_PATH}")
print(f"  存在: {os.path.exists(DOC_PATH)}")
print(f"  大小: {os.path.getsize(DOC_PATH)} bytes")

with open(DOC_PATH, "rb") as f:
    files = {"file": ("20221125092539.doc", f, "application/msword")}
    r = requests.post(f"{API}/rules/from-template", files=files, timeout=120)

print(f"  状态码: {r.status_code}")
if r.status_code != 200:
    print(f"  错误: {r.text[:200]}")
    sys.exit(1)

result = r.json()
print(f"  方法: {result.get('method')}")
print(f"  文件格式: {result.get('file_format')}")
print(f"  文本框数量: {result.get('textbox_count')}")
print(f"  有文本框要求: {result.get('has_textbox_requirements')}")

check("API 返回 200", r.status_code == 200)
check("文件格式识别为 doc", result.get("file_format") == "doc")
check("检测到文本框", result.get("textbox_count", 0) > 0, ">0", str(result.get("textbox_count")))
check("文本框含格式要求", result.get("has_textbox_requirements", False))

# Step 2: Verify text box content
print("\n【Step 2】文本框内容验证")
textbox_texts = result.get("textbox_texts", [])
print(f"  文本框内容数: {len(textbox_texts)}")

key_phrases = [
    ("三号黑体", "标题字号字体"),
    ("五号宋体", "正文字号字体"),
    ("首行缩进", "缩进要求"),
    ("单倍行距", "行距要求"),
    ("居中", "对齐要求"),
    ("加粗", "加粗要求"),
    ("Times New Roman", "英文字体"),
    ("参考文献", "参考文献样式"),
]

for phrase, desc in key_phrases:
    found = any(phrase in tb for tb in textbox_texts)
    check(f"文本框含'{phrase}' ({desc})", found)

# Step 3: Verify extracted rules
print("\n【Step 3】提取的格式规则验证")
rules = result["rule_set"]
styles = rules.get("styles", {})
print(f"  样式数: {len(styles)}")
print(f"  样式列表: {list(styles.keys())}")

sources = rules.get("sources", {})
print(f"  来源标注: {sources}")

# Check Title style
t = styles.get("Title", {})
if t:
    tf = t.get("font", {})
    tp = t.get("paragraph", {})
    check("Title: 黑体", tf.get("font_name_east_asia") == "黑体", "黑体", str(tf.get("font_name_east_asia")))
    check("Title: 三号(16pt)", tf.get("font_size") == 16.0, "16pt", str(tf.get("font_size")))
    check("Title: 加粗", tf.get("bold") == True)
    check("Title: 居中", tp.get("alignment") == "center", "center", str(tp.get("alignment")))

# Check Heading1
h1 = styles.get("Heading1", {})
if h1:
    h1f = h1.get("font", {})
    h1p = h1.get("paragraph", {})
    check("H1: 黑体", h1f.get("font_name_east_asia") == "黑体")
    check("H1: 三号(16pt)", h1f.get("font_size") == 16.0, "16pt", str(h1f.get("font_size")))
    check("H1: 加粗", h1f.get("bold") == True)

# Check Body
b = styles.get("Body", {})
if b:
    bf = b.get("font", {})
    bp = b.get("paragraph", {})
    check("Body: 宋体", bf.get("font_name_east_asia") == "宋体")
    check("Body: 五号(10.5pt)", bf.get("font_size") == 10.5, "10.5pt", str(bf.get("font_size")))
    check("Body: 首行缩进24pt", bp.get("first_line_indent") == 24.0, "24pt", str(bp.get("first_line_indent")))
    check("Body: 单倍行距", bp.get("line_spacing") == 1.0, "1.0", str(bp.get("line_spacing")))

# Check Reference
ref = styles.get("Reference", {})
if ref:
    rf = ref.get("font", {})
    rp = ref.get("paragraph", {})
    check("Reference: 宋体", rf.get("font_name_east_asia") == "宋体")
    check("Reference: 五号(10.5pt)", rf.get("font_size") == 10.5, "10.5pt", str(rf.get("font_size")))
else:
    check("Reference 样式存在", False, "存在", "不存在")

# Check source annotations — should have "textbox" sources
textbox_sources = [k for k, v in sources.items() if v == "textbox"]
print(f"\n  文本框来源样式: {textbox_sources}")
check("有文本框来源标注", len(textbox_sources) > 0)

# Step 4: Generate document with these rules
print("\n【Step 4】用提取的规则生成文档")
DRAFT_PATH = os.path.join(BASE, "user_real_doc.docx")
if os.path.exists(DRAFT_PATH):
    rules_json = json.dumps(rules, ensure_ascii=False)
    with open(DRAFT_PATH, "rb") as f:
        files = {"file": ("论文.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        data = {"rules_json": rules_json, "skip_optimization": "true"}
        r = requests.post(f"{API}/optimize/generate", files=files, data=data, timeout=60)
    
    print(f"  状态码: {r.status_code}")
    print(f"  文件大小: {len(r.content)} bytes")
    check("生成成功", r.status_code == 200)
    check("文件非空", len(r.content) > 30000)
    
    if r.status_code == 200:
        out_path = os.path.join(BASE, "sjtu_thesis_output.docx")
        with open(out_path, "wb") as f:
            f.write(r.content)
        print(f"  保存到: {out_path}")
else:
    print("  跳过：未找到草稿文件")

print(f"\n{'=' * 70}")
print(f"  端到端测试结果: 通过={PASS} 失败={FAIL} 总计={PASS+FAIL}")
print(f"{'=' * 70}")
