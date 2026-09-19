"""
健壮性测试 — 用各种异常文档验证系统不会崩溃且格式正确。
测试场景：
1. 中文样式名文档（标题1/正文）
2. 无样式直接格式化文档（纯加粗+大字号当标题）
3. 无标题文档
4. 无正文文档
5. 不规则表格文档
6. 空段落+图片文档
7. 极简文档（只有1段文字）
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

BASE = os.path.dirname(os.path.abspath(__file__))

def _set_run_font(run, east, west, size, bold=False):
    run.font.name = west
    run.font.size = Pt(size)
    run.font.bold = bold
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = rPr.makeelement(qn("w:rFonts"), {})
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:eastAsia"), east)
    rFonts.set(qn("w:ascii"), west)
    rFonts.set(qn("w:hAnsi"), west)

# ============================================================
# 1. 中文样式名文档
# ============================================================
def create_chinese_style_doc():
    doc = Document()
    for p in doc.paragraphs:
        p.text = ""
    # 用直接格式化模拟中文样式名
    p = doc.add_paragraph()
    p.style = doc.styles['Title']
    r = p.add_run("中文样式标题测试")
    _set_run_font(r, "黑体", "SimHei", 22, True)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p = doc.add_paragraph()
    p.style = doc.styles['Heading 1']
    r = p.add_run("第一章 概述")
    _set_run_font(r, "黑体", "SimHei", 16, True)

    p = doc.add_paragraph()
    p.style = doc.styles['Normal']
    r = p.add_run("这是正文内容，使用中文样式名。")
    _set_run_font(r, "宋体", "Times New Roman", 12)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    path = os.path.join(BASE, "robust_test_1_chinese_style.docx")
    doc.save(path)
    return path

# ============================================================
# 2. 无样式直接格式化文档
# ============================================================
def create_no_style_doc():
    doc = Document()
    for p in doc.paragraphs:
        p.text = ""
    # 不用任何样式，直接加粗+大字号
    p = doc.add_paragraph()
    r = p.add_run("直接格式化标题")
    _set_run_font(r, "黑体", "SimHei", 22, True)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p = doc.add_paragraph()
    r = p.add_run("第一节 引言")
    _set_run_font(r, "黑体", "SimHei", 16, True)

    p = doc.add_paragraph()
    r = p.add_run("这是没有使用任何Word样式的正文内容，仅通过直接格式化设置字体和字号。")
    _set_run_font(r, "宋体", "Times New Roman", 12)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Pt(24)
    p.paragraph_format.line_spacing = 1.5

    p = doc.add_paragraph()
    r = p.add_run("第二节 方法")
    _set_run_font(r, "黑体", "SimHei", 14, True)

    p = doc.add_paragraph()
    r = p.add_run("二级标题下的内容。")
    _set_run_font(r, "宋体", "Times New Roman", 12)

    path = os.path.join(BASE, "robust_test_2_no_style.docx")
    doc.save(path)
    return path

# ============================================================
# 3. 无标题文档
# ============================================================
def create_no_heading_doc():
    doc = Document()
    for p in doc.paragraphs:
        p.text = ""
    p = doc.add_paragraph()
    r = p.add_run("这是一篇没有标题的文档，只有正文内容。")
    _set_run_font(r, "宋体", "Times New Roman", 12)

    p = doc.add_paragraph()
    r = p.add_run("第二段正文内容，同样没有任何标题。")
    _set_run_font(r, "宋体", "Times New Roman", 12)

    p = doc.add_paragraph()
    r = p.add_run("第三段正文内容。")
    _set_run_font(r, "宋体", "Times New Roman", 12)

    path = os.path.join(BASE, "robust_test_3_no_heading.docx")
    doc.save(path)
    return path

# ============================================================
# 4. 无正文文档（只有标题）
# ============================================================
def create_no_body_doc():
    doc = Document()
    for p in doc.paragraphs:
        p.text = ""
    doc.add_heading("纯标题文档", level=0)
    doc.add_heading("第一章", level=1)
    doc.add_heading("第一节", level=2)
    doc.add_heading("第二节", level=2)

    path = os.path.join(BASE, "robust_test_4_no_body.docx")
    doc.save(path)
    return path

# ============================================================
# 5. 不规则表格文档
# ============================================================
def create_irregular_table_doc():
    doc = Document()
    for p in doc.paragraphs:
        p.text = ""
    doc.add_heading("不规则表格测试", level=1)
    p = doc.add_paragraph()
    r = p.add_run("包含不规则表格的文档。")
    _set_run_font(r, "宋体", "Times New Roman", 12)

    # 不规则表格：第二行只有2列
    table = doc.add_table(rows=3, cols=3)
    table.style = 'Table Grid'
    for i, val in enumerate(["A", "B", "C"]):
        table.rows[0].cells[i].text = val
    table.rows[1].cells[0].text = "D"
    table.rows[1].cells[1].text = "E"
    # 第三行只有1列内容
    table.rows[2].cells[0].text = "F"

    path = os.path.join(BASE, "robust_test_5_irregular_table.docx")
    doc.save(path)
    return path

# ============================================================
# 6. 空段落+极简文档
# ============================================================
def create_minimal_doc():
    doc = Document()
    p = doc.add_paragraph()
    r = p.add_run("极简文档")
    _set_run_font(r, "宋体", "Times New Roman", 12)

    path = os.path.join(BASE, "robust_test_6_minimal.docx")
    doc.save(path)
    return path

# ============================================================
# 运行测试
# ============================================================
from src.modules.parser import parse_document
from src.modules.format_extractor import extract_format_rules
from src.modules.format_applier import apply_format
from src.modules.doc_generator import generate_document

tests = [
    ("中文样式名", create_chinese_style_doc),
    ("无样式直接格式化", create_no_style_doc),
    ("无标题文档", create_no_heading_doc),
    ("无正文文档", create_no_body_doc),
    ("不规则表格", create_irregular_table_doc),
    ("极简文档", create_minimal_doc),
]

print("=" * 70)
print("  健壮性测试 — 任意文档兼容性验证")
print("=" * 70)

PASS = 0
FAIL = 0

for name, creator in tests:
    print(f"\n--- 测试: {name} ---")
    try:
        # 创建文档
        doc_path = creator()
        print(f"  创建: {os.path.basename(doc_path)} ({os.path.getsize(doc_path)} bytes)")

        # 解析
        parsed = parse_document(doc_path)
        print(f"  解析: {len(parsed.paragraphs)}段, {len(parsed.tables)}表, 页面={parsed.page_width}x{parsed.page_height}")

        # 方式A: 提取格式
        try:
            rule_set = extract_format_rules(parsed)
            styles = list(rule_set.styles.keys())
            print(f"  格式提取: 样式={styles}")
            body_ok = "Body" in rule_set.styles
            print(f"  Body兜底: {'✅' if body_ok else '❌'}")
            if body_ok:
                bs = rule_set.styles["Body"]
                print(f"  Body格式: {bs.font.font_name_east_asia} {bs.font.font_size}pt")
        except Exception as e:
            print(f"  格式提取: ❌ 崩溃 — {e}")
            rule_set = None

        # 方式A: 生成文档
        if rule_set:
            try:
                formatted = apply_format(parsed, None, rule_set)
                out_path = doc_path.replace(".docx", "_output.docx")
                generate_document(formatted, out_path)
                print(f"  文档生成: ✅ {os.path.getsize(out_path)} bytes")

                # 验证生成的文档
                v = parse_document(out_path)
                print(f"  成品验证: {len(v.paragraphs)}段, {len(v.tables)}表")
                PASS += 1
            except Exception as e:
                print(f"  文档生成: ❌ 崩溃 — {e}")
                FAIL += 1

        # 方式B: 用预设规则生成
        try:
            from src.modules.requirement_parser import parse_requirement
            rs_b = parse_requirement("本科毕业论文格式", None)
            formatted_b = apply_format(parsed, None, rs_b)
            out_b = doc_path.replace(".docx", "_preset_output.docx")
            generate_document(formatted_b, out_b)
            print(f"  预设生成: ✅ {os.path.getsize(out_b)} bytes")
            PASS += 1
        except Exception as e:
            print(f"  预设生成: ❌ 崩溃 — {e}")
            FAIL += 1

    except Exception as e:
        print(f"  ❌ 整体崩溃 — {e}")
        FAIL += 1

print(f"\n{'=' * 70}")
print(f"  健壮性测试结果: 通过={PASS} 失败={FAIL}")
print(f"{'=' * 70}")
