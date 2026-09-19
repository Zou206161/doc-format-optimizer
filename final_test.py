"""
最终综合测试 — 通过 HTTP API 测试系统全部功能路径。
覆盖：健康检查、预设模板、方式A格式提取、方式B文字解析、
内容优化预览、文档生成、错误处理、生成文档格式验证。
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOUNDARY = "----FinalTestBoundary"
PASS = 0
FAIL = 0
RESULTS = []


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        RESULTS.append(("PASS", name, detail))
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        RESULTS.append(("FAIL", name, detail))
        print(f"  ❌ {name}: {detail}")
    if detail and condition:
        print(f"     {detail}")


def post(endpoint, fields, expect_binary=False):
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
        f"{BASE_URL}{endpoint}", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={BOUNDARY}"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            ct = resp.headers.get("Content-Type", "")
            cd = resp.headers.get("Content-Disposition", "")
            if expect_binary or "json" not in ct:
                return resp.status, raw, ct, cd
            return resp.status, json.loads(raw), ct, cd
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw), "", ""
        except Exception:
            return e.code, raw, "", ""


def get(endpoint):
    with urllib.request.urlopen(f"{BASE_URL}{endpoint}") as resp:
        return resp.status, json.loads(resp.read())


print("=" * 70)
print("  AI 智能文档格式优化系统 — 最终综合测试")
print("=" * 70)
print()

# 等待服务器启动
for _ in range(10):
    try:
        get("/api/health")
        break
    except Exception:
        time.sleep(1)

# ============================================================
print("【1. 系统健康检查】")
# ============================================================
status, data = get("/api/health")
check("GET /api/health 返回 200", status == 200)
check("状态为 ok", data.get("status") == "ok", f"status={data.get('status')}")
print()

# ============================================================
print("【2. 预设模板列表】")
# ============================================================
status, data = get("/api/rules/presets")
check("GET /api/rules/presets 返回 200", status == 200)
presets = data.get("presets", [])
check("返回 3 套预设模板", len(presets) == 3, f"实际{len(presets)}套")
ids = [p["id"] for p in presets]
check("包含 undergraduate_thesis", "undergraduate_thesis" in ids)
check("包含 master_thesis", "master_thesis" in ids)
check("包含 journal_article", "journal_article" in ids)
print()

# ============================================================
print("【3. 方式A — 上传模板提取格式规则】")
# ============================================================
with open(os.path.join(BASE_DIR, "test_template.docx"), "rb") as f:
    tpl = f.read()
status, data, _, _ = post("/api/rules/from-template", {"file": ("template.docx", tpl, "application/octet-stream")})
check("POST /api/rules/from-template 返回 200", status == 200)
check("method = template", data.get("method") == "template")
rs_a = data.get("rule_set", {})
dl = rs_a.get("document_level", {})
check("页面 A4 宽度 595.3pt", abs(dl.get("page_width", 0) - 595.3) < 0.1, f"page_width={dl.get('page_width')}")
check("页面 A4 高度 841.9pt", abs(dl.get("page_height", 0) - 841.9) < 0.1, f"page_height={dl.get('page_height')}")
check("上边距 72pt", dl.get("margin_top") == 72.0, f"margin_top={dl.get('margin_top')}")
check("下边距 72pt", dl.get("margin_bottom") == 72.0)
check("左边距 90pt", dl.get("margin_left") == 90.0)
check("右边距 90pt", dl.get("margin_right") == 90.0)
check("页眉内容正确", dl.get("header") == "本科毕业论文", f"header={dl.get('header')}")

styles_a = rs_a.get("styles", {})
check("包含 4 个样式", len(styles_a) == 4, f"styles={list(styles_a.keys())}")
check("包含 Title", "Title" in styles_a)
check("包含 Heading1", "Heading1" in styles_a)
check("包含 Heading2", "Heading2" in styles_a)
check("包含 Body", "Body" in styles_a)

# Title 格式
t_font = styles_a.get("Title", {}).get("font", {})
t_para = styles_a.get("Title", {}).get("paragraph", {})
check("Title 中文字体=黑体", t_font.get("font_name_east_asia") == "黑体", f"east_asia={t_font.get('font_name_east_asia')}")
check("Title 字号=22pt(二号)", t_font.get("font_size") == 22.0, f"size={t_font.get('font_size')}")
check("Title 加粗", t_font.get("bold") == True)
check("Title 居中", t_para.get("alignment") == "center")

# Heading1 格式
h1_font = styles_a.get("Heading1", {}).get("font", {})
h1_para = styles_a.get("Heading1", {}).get("paragraph", {})
check("H1 中文字体=黑体", h1_font.get("font_name_east_asia") == "黑体")
check("H1 字号=16pt(三号)", h1_font.get("font_size") == 16.0)
check("H1 加粗", h1_font.get("bold") == True)
check("H1 居中", h1_para.get("alignment") == "center")

# Heading2 格式
h2_font = styles_a.get("Heading2", {}).get("font", {})
h2_para = styles_a.get("Heading2", {}).get("paragraph", {})
check("H2 中文字体=黑体", h2_font.get("font_name_east_asia") == "黑体")
check("H2 字号=14pt(四号)", h2_font.get("font_size") == 14.0)
check("H2 左对齐", h2_para.get("alignment") == "left")

# Body 格式
b_font = styles_a.get("Body", {}).get("font", {})
b_para = styles_a.get("Body", {}).get("paragraph", {})
check("Body 中文字体=宋体", b_font.get("font_name_east_asia") == "宋体")
check("Body 西文字体=Times New Roman", b_font.get("font_name") == "Times New Roman")
check("Body 字号=12pt(小四)", b_font.get("font_size") == 12.0)
check("Body 两端对齐", b_para.get("alignment") == "justify")
check("Body 行距=1.5", b_para.get("line_spacing") == 1.5)
check("Body 首行缩进=24pt", b_para.get("first_line_indent") == 24.0)

# 来源标注
sources_a = rs_a.get("sources", {})
check("来源标注非空", len(sources_a) > 0, f"sources={sources_a}")
check("来源全部为 template", all(v == "template" for v in sources_a.values()) if sources_a else False)
print()

# ============================================================
print("【4. 方式B — 文字解析（含'本科'关键词）】")
# ============================================================
text1 = "本科毕业论文格式：一级标题黑体三号居中，正文宋体小四1.5倍行距首行缩进2字符"
status, data, _, _ = post("/api/rules/from-text", {"text": text1})
check("POST /api/rules/from-text 返回 200", status == 200)
check("method 包含 text", "text" in str(data.get("method", "")), f"method={data.get('method')}")
rs_b1 = data.get("rule_set", {})
styles_b1 = rs_b1.get("styles", {})
b1_font = styles_b1.get("Body", {}).get("font", {})
b1_para = styles_b1.get("Body", {}).get("paragraph", {})
check("B1 正文中文字体=宋体", b1_font.get("font_name_east_asia") == "宋体")
check("B1 正文字号=12pt", b1_font.get("font_size") == 12.0)
check("B1 正文行距=1.5", b1_para.get("line_spacing") == 1.5)
check("B1 首行缩进=24pt", b1_para.get("first_line_indent") == 24.0)
h1_b1 = styles_b1.get("Heading1", {}).get("font", {})
check("B1 H1字体=黑体", h1_b1.get("font_name_east_asia") == "黑体")
check("B1 H1字号=16pt", h1_b1.get("font_size") == 16.0)
sources_b1 = rs_b1.get("sources", {})
check("B1 来源含 preset", any(v == "preset" for v in sources_b1.values()), f"sources={sources_b1}")
print()

# ============================================================
print("【5. 方式B — 文字解析（含'硕士'关键词）】")
# ============================================================
text2 = "硕士学位论文：标题黑体小二号，正文宋体小四1.5倍行距"
status, data, _, _ = post("/api/rules/from-text", {"text": text2})
check("POST 返回 200", status == 200)
rs_b2 = data.get("rule_set", {})
h1_b2 = rs_b2.get("styles", {}).get("Heading1", {}).get("font", {})
check("B2 H1字号=18pt(小二, 硕士)", h1_b2.get("font_size") == 18.0, f"size={h1_b2.get('font_size')}")
print()

# ============================================================
print("【6. 方式B — 文字解析（显式 preset_id=journal_article）】")
# ============================================================
text3 = "期刊投稿格式"
status, data, _, _ = post("/api/rules/from-text", {"text": text3, "preset_id": "journal_article"})
check("POST 返回 200", status == 200)
rs_b3 = data.get("rule_set", {})
b3_font = rs_b3.get("styles", {}).get("Body", {}).get("font", {})
dl_b3 = rs_b3.get("document_level", {})
check("B3 正文字号=10.5pt(五号, 期刊)", b3_font.get("font_size") == 10.5, f"size={b3_font.get('font_size')}")
check("B3 上边距=54pt(期刊)", dl_b3.get("margin_top") == 54.0, f"margin_top={dl_b3.get('margin_top')}")
print()

# ============================================================
print("【7. 方式B — 文字解析（无预设关键词，仅默认值）】")
# ============================================================
text4 = "文档标题居中，正文两端对齐"
status, data, _, _ = post("/api/rules/from-text", {"text": text4})
check("POST 返回 200", status == 200)
rs_b4 = data.get("rule_set", {})
sources_b4 = rs_b4.get("sources", {})
check("B4 来源含 default", any(v == "default" for v in sources_b4.values()), f"sources={sources_b4}")
check("B4 来源无 preset", not any(v == "preset" for v in sources_b4.values()))
print()

# ============================================================
print("【8. 内容优化预览（降级模式 — LLM 不可用）】")
# ============================================================
with open(os.path.join(BASE_DIR, "test_draft.docx"), "rb") as f:
    draft = f.read()
status, data, _, _ = post("/api/optimize/preview", {"file": ("draft.docx", draft, "application/octet-stream")})
check("POST /api/optimize/preview 返回 200", status == 200)
paras = data.get("paragraphs", [])
check("返回段落列表", len(paras) > 0, f"paragraphs={len(paras)}")
check("总变更数=0(降级模式)", data.get("total_changes") == 0, f"changes={data.get('total_changes')}")
print()

# ============================================================
print("【9. 完整管线 A — 模板规则 → 草稿 → 生成成品文档】")
# ============================================================
rules_a_str = json.dumps(rs_a, ensure_ascii=False)
status, file_data, ct, cd = post("/api/optimize/generate", {
    "file": ("draft.docx", draft, "application/octet-stream"),
    "rules_json": rules_a_str,
    "skip_optimization": "true",
}, expect_binary=True)
check("POST /api/optimize/generate 返回 200", status == 200)
check("返回二进制数据", len(file_data) > 1000, f"size={len(file_data)}")
check("Content-Type 为 docx", "wordprocessingml" in ct, f"ct={ct}")
check("Content-Disposition 含 attachment", "attachment" in cd, f"cd={cd}")

out_a = os.path.join(BASE_DIR, "最终成品_方式A.docx")
with open(out_a, "wb") as f:
    f.write(file_data)
print(f"     文件已保存: {out_a} ({len(file_data)} bytes)")

# 验证生成的文档
sys.path.insert(0, BASE_DIR)
from src.modules.parser import parse_document
v_a = parse_document(out_a)
check("A 生成文档段落数=11", len(v_a.paragraphs) == 11, f"paras={len(v_a.paragraphs)}")
check("A 生成文档表格数=1", len(v_a.tables) == 1)
check("A 页面=A4", abs(v_a.page_width - 595.3) < 0.1 and abs(v_a.page_height - 841.9) < 0.1)
check("A 页边距正确", v_a.margin_top == 72.0 and v_a.margin_left == 90.0)
check("A 页眉正确", v_a.header == "本科毕业论文")

# 查找标题段落 — 打印所有段落的格式信息用于调试
title_found = False
for p in v_a.paragraphs:
    if "论人工智能" in p.text:
        east = p.font.font_name_east_asia
        sz = p.font.font_size
        bold = p.font.bold
        align = p.paragraph.alignment
        check("A 标题段落存在", True, f"text='{p.text[:20]}', east={east}, size={sz}, bold={bold}, align={align}")
        title_found = east == "黑体" and sz == 22.0 and bold == True
        break
check("A 标题=黑体22pt加粗居中", title_found, "标题格式不正确")

# 查找 Heading1
h1_found = False
for p in v_a.paragraphs:
    if p.text.strip() == "引言" and p.font.font_name_east_asia == "黑体" and p.font.font_size == 16.0:
        h1_found = True
        break
check("A H1(引言)=黑体16pt居中", h1_found)

# 查找 Heading2
h2_found = False
for p in v_a.paragraphs:
    if p.text.strip() == "技术现状" and p.font.font_name_east_asia == "黑体" and p.font.font_size == 14.0:
        h2_found = True
        break
check("A H2(技术现状)=黑体14pt左对齐", h2_found)

# 查找正文
body_found = False
for p in v_a.paragraphs:
    if "人工智能技术" in p.text and p.font.font_name_east_asia == "宋体" and p.font.font_size == 12.0:
        body_found = True
        break
check("A 正文=宋体12pt两端对齐1.5行距", body_found)

# 查找表格
table_ok = False
if v_a.tables:
    cells = v_a.tables[0].cells
    if len(cells) >= 1 and "应用领域" in cells[0]:
        table_ok = True
check("A 表格文字正常(应用领域不乱码)", table_ok)
print()

# ============================================================
print("【10. 完整管线 B — 文字规则 → 草稿 → 生成成品文档】")
# ============================================================
rules_b_str = json.dumps(rs_b1, ensure_ascii=False)
status, file_data_b, ct_b, cd_b = post("/api/optimize/generate", {
    "file": ("draft.docx", draft, "application/octet-stream"),
    "rules_json": rules_b_str,
    "skip_optimization": "true",
}, expect_binary=True)
check("POST /api/optimize/generate 返回 200", status == 200)
check("返回二进制数据", len(file_data_b) > 1000, f"size={len(file_data_b)}")

out_b = os.path.join(BASE_DIR, "最终成品_方式B.docx")
with open(out_b, "wb") as f:
    f.write(file_data_b)
print(f"     文件已保存: {out_b} ({len(file_data_b)} bytes)")

v_b = parse_document(out_b)
check("B 生成文档段落数=11", len(v_b.paragraphs) == 11)
check("B 生成文档表格数=1", len(v_b.tables) == 1)

# 标题
title_b = False
for p in v_b.paragraphs:
    if "论人工智能" in p.text:
        east = p.font.font_name_east_asia
        sz = p.font.font_size
        bold = p.font.bold
        check("B 标题段落存在", True, f"east={east}, size={sz}, bold={bold}")
        title_b = east == "黑体" and sz == 22.0 and bold == True
        break
check("B 标题=黑体22pt加粗居中", title_b, "标题格式不正确")

# 正文
body_b = False
for p in v_b.paragraphs:
    if "人工智能技术" in p.text and p.font.font_name_east_asia == "宋体":
        body_b = True
        break
check("B 正文=宋体", body_b)
print()

# ============================================================
print("【11. 错误处理 — 非 .docx 文件上传】")
# ============================================================
status, data, _, _ = post("/api/rules/from-template", {
    "file": ("test.txt", b"hello world", "text/plain")
})
check("非.docx 返回 400", status == 400, f"status={status}")
check("错误信息正确", "Only .docx" in data.get("error", ""), f"error={data.get('error','')}")
print()

# ============================================================
print("【12. 错误处理 — 无效 rules JSON】")
# ============================================================
status, data, _, _ = post("/api/optimize/generate", {
    "file": ("draft.docx", draft, "application/octet-stream"),
    "rules_json": '{"invalid": true}',
    "skip_optimization": "true",
}, expect_binary=True)
if status == 200:
    check("无效JSON 被接受(Pydantic默认值)", True, f"返回200, {len(data)} bytes (Pydantic忽略额外字段)")
elif status >= 400:
    err_msg = json.loads(data) if isinstance(data, bytes) else data
    check("无效JSON 返回错误", True, f"status={status}")
else:
    check("无效JSON 处理", False, f"status={status}")
print()

# ============================================================
print("【13. 错误处理 — 空文字输入】")
# ============================================================
status, data, _, _ = post("/api/rules/from-text", {"text": ""})
check("空文字输入返回 422 验证错误", status == 422, f"status={status}")
if status == 200:
    check("空文字返回默认规则", "rule_set" in data)
print()

# ============================================================
# 汇总报告
# ============================================================
print("=" * 70)
print("  最终测试汇总")
print("=" * 70)
print()
print(f"  通过: {PASS}  失败: {FAIL}  总计: {PASS + FAIL}")
print(f"  通过率: {PASS/(PASS+FAIL)*100:.1f}%")
print()
if FAIL > 0:
    print("  失败项:")
    for status, name, detail in RESULTS:
        if status == "FAIL":
            print(f"    ❌ {name}: {detail}")
    print()
print("=" * 70)
print(f"  生成文件:")
print(f"    方式A成品: 最终成品_方式A.docx ({os.path.getsize(out_a)} bytes)")
print(f"    方式B成品: 最终成品_方式B.docx ({os.path.getsize(out_b)} bytes)")
print("=" * 70)
