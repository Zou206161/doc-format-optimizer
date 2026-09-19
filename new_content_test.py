"""
新内容端到端测试 — 人工智能在日常生活领域的研究应用报告
创建新模板+新草稿，走方式A和方式B完整管线，验证格式和内容。
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx import Document
from docx.shared import Pt, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

BASE = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 1. 创建新模板文档
# ============================================================
def create_template():
    doc = Document()

    # 页面设置
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.17)
    section.right_margin = Cm(3.17)

    # 默认字体
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)
    style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    # 页眉
    header = section.header
    hp = header.paragraphs[0]
    hp.text = "人工智能应用研究"
    hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in hp.runs:
        run.font.size = Pt(9)

    # Title 样式段落
    p = doc.add_paragraph()
    p.style = doc.styles['Title']
    run = p.add_run("模板标题")
    run.font.name = 'SimHei'
    run.font.size = Pt(22)
    run.font.bold = True
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Heading 1
    p = doc.add_paragraph()
    p.style = doc.styles['Heading 1']
    run = p.add_run("一级标题")
    run.font.name = 'SimHei'
    run.font.size = Pt(16)
    run.font.bold = True
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.space_before = Pt(24)
    pf.space_after = Pt(18)

    # Heading 2
    p = doc.add_paragraph()
    p.style = doc.styles['Heading 2']
    run = p.add_run("二级标题")
    run.font.name = 'SimHei'
    run.font.size = Pt(14)
    run.font.bold = True
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf = p.paragraph_format
    pf.space_before = Pt(18)
    pf.space_after = Pt(12)

    # Body
    p = doc.add_paragraph()
    p.style = doc.styles['Normal']
    run = p.add_run("正文内容。")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format
    pf.line_spacing = 1.5
    pf.first_line_indent = Pt(24)

    # 表格
    table = doc.add_table(rows=2, cols=3)
    table.style = 'Table Grid'
    headers = ['类别', '应用场景', '技术']
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
    row2 = ['语音', '智能助手', 'NLP']
    for i, v in enumerate(row2):
        table.rows[1].cells[i].text = v

    path = os.path.join(BASE, "new_template.docx")
    doc.save(path)
    return path

# ============================================================
# 2. 创建新草稿文档（含口语化表达和错别字）
# ============================================================
def create_draft():
    doc = Document()

    # 标题（Normal样式，测试标题检测）
    p = doc.add_paragraph()
    p.style = doc.styles['Normal']
    run = p.add_run("人工智能在日常生活中的应用研究")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    # 引言
    doc.add_heading("引言", level=1)

    p = doc.add_paragraph()
    p.style = doc.styles['Normal']
    run = p.add_run("现在的人工智能技术已经深入到我们日常生活的方方面面了，从早上起床用的智能闹钟到晚上睡觉前的推荐系统，AI无处不在。")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    p = doc.add_paragraph()
    p.style = doc.styles['Normal']
    run = p.add_run("但是呢，很多人其实并不了解这些技术背后是咋回事，本文将从几个主要的应用领域来探讨一下这个问题。")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    # 智能家居
    doc.add_heading("智能家居系统", level=1)
    doc.add_heading("智能音箱与语音助手", level=2)

    p = doc.add_paragraph()
    p.style = doc.styles['Normal']
    run = p.add_run("智能音箱是现在最普遍的AI应用之一，像小爱同学、天猫精灵这些产品已经进入了很多家庭。")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    p = doc.add_paragraph()
    p.style = doc.styles['Normal']
    run = p.add_run("这些设备主要用了自然语言处理和语音识别技术，能够理解用户的指令并执行相应的操作，比如说放音乐、设闹钟啥的。")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    # 表格：AI应用场景对比
    doc.add_heading("主要应用场景对比", level=2)

    table = doc.add_table(rows=4, cols=3)
    table.style = 'Table Grid'
    data = [
        ['应用领域', '代表产品', '核心技术'],
        ['智能语音', '小爱同学/天猫精灵', 'NLP + ASR'],
        ['智能视觉', '人脸识别门禁', 'CNN + 目标检测'],
        ['推荐系统', '短视频/购物推荐', '协同过滤 + 深度学习'],
    ]
    for i, row in enumerate(data):
        for j, val in enumerate(row):
            table.rows[i].cells[j].text = val

    # 智能交通
    doc.add_heading("智能交通与出行", level=1)

    p = doc.add_paragraph()
    p.style = doc.styles['Normal']
    run = p.add_run("导航软件用AI来预测路况和拥堵情况，这个技术已经非常成熟了。")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    p = doc.add_paragraph()
    p.style = doc.styles['Normal']
    run = p.add_run("自动驾驶技术也在快速发展中，虽然目前还存在着不少问题，但是未来的前景是非常广阔的。")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    # 结论
    doc.add_heading("结论与展望", level=1)

    p = doc.add_paragraph()
    p.style = doc.styles['Normal']
    run = p.add_run("总的来说呢，人工智能技术在日常生活中的应用已经非常广泛了，给人们带来了很多便利。")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    p = doc.add_paragraph()
    p.style = doc.styles['Normal']
    run = p.add_run("未来的发展趋势是更加智能化和个性化，但同时也需要注意隐私保护和伦理问题这些方面。")
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

    path = os.path.join(BASE, "new_draft.docx")
    doc.save(path)
    return path

# ============================================================
# 3. 执行测试
# ============================================================
print("=" * 70)
print("  新内容端到端测试 — 人工智能在日常生活领域的研究应用")
print("=" * 70)

# 创建文档
print("\n[1] 创建测试文档...")
tpl_path = create_template()
draft_path = create_draft()
print(f"  模板: {tpl_path} ({os.path.getsize(tpl_path)} bytes)")
print(f"  草稿: {draft_path} ({os.path.getsize(draft_path)} bytes)")
print(f"  草稿内容: 人工智能在日常生活中的应用研究")
print(f"  草稿特点: 含口语化表达('但是呢','咋回事','啥的')、含表格(3×3)")

# 解析草稿
print("\n[2] 解析草稿内容...")
from src.modules.parser import parse_document
draft_doc = parse_document(draft_path)
print(f"  段落数: {len(draft_doc.paragraphs)}")
print(f"  表格数: {len(draft_doc.tables)}")
for p in draft_doc.paragraphs:
    t = p.text[:50] + "..." if len(p.text) > 50 else p.text
    tag = " [Heading]" if p.is_heading else ""
    print(f"  para{p.index} [{p.style_name}]{tag}: {t}")

# 方式A：模板提取
print("\n[3] 方式A — 模板格式提取...")
from src.modules.format_extractor import extract_format_rules
tpl_doc = parse_document(tpl_path)
rs_a = extract_format_rules(tpl_doc)
styles = list(rs_a.styles.keys())
print(f"  样式: {styles}")
print(f"  页面: {rs_a.document_level.page_width}x{rs_a.document_level.page_height}pt")
print(f"  页眉: '{rs_a.document_level.header}'")
for sk in ["Title", "Heading1", "Heading2", "Body"]:
    if sk in rs_a.styles:
        s = rs_a.styles[sk]
        f = s.font
        p = s.paragraph
        print(f"  {sk}: {f.font_name_east_asia}/{f.font_name} {f.font_size}pt bold={f.bold} align={p.alignment} ls={p.line_spacing} indent={p.first_line_indent}")

# 方式A：格式套用+生成
print("\n[4] 方式A — 格式套用 + 文档生成...")
from src.modules.format_applier import apply_format
from src.modules.doc_generator import generate_document
formatted_a = apply_format(draft_doc, None, rs_a)
print(f"  样式映射:")
for fp in formatted_a.paragraphs:
    t = fp.text[:40] + "..." if len(fp.text) > 40 else fp.text
    print(f"    {fp.style_key:10s} | {t}")
out_a = os.path.join(BASE, "新内容_成品_方式A.docx")
generate_document(formatted_a, out_a)
print(f"  生成: {out_a} ({os.path.getsize(out_a)} bytes)")

# 方式B：文字解析
print("\n[5] 方式B — 文字解析...")
from src.modules.requirement_parser import parse_requirement
text_req = "本科毕业论文：标题黑体二号居中加粗，一级标题黑体三号居中，二级标题黑体四号左对齐，正文宋体小四1.5倍行距首行缩进2字符"
rs_b = parse_requirement(text_req, None)
print(f"  样式: {list(rs_b.styles.keys())}")
sources_b = rs_b.sources if hasattr(rs_b, 'sources') else {}
preset_srcs = [k for k, v in sources_b.items() if v == "preset"]
default_srcs = [k for k, v in sources_b.items() if v == "default"]
print(f"  预设来源项: {len(preset_srcs)}")
print(f"  默认来源项: {len(default_srcs)}")
for sk in ["Title", "Heading1", "Heading2", "Body"]:
    if sk in rs_b.styles:
        s = rs_b.styles[sk]
        f = s.font
        p = s.paragraph
        print(f"  {sk}: {f.font_name_east_asia}/{f.font_name} {f.font_size}pt bold={f.bold} align={p.alignment} ls={p.line_spacing} indent={p.first_line_indent}")

# 方式B：格式套用+生成
print("\n[6] 方式B — 格式套用 + 文档生成...")
formatted_b = apply_format(draft_doc, None, rs_b)
out_b = os.path.join(BASE, "新内容_成品_方式B.docx")
generate_document(formatted_b, out_b)
print(f"  生成: {out_b} ({os.path.getsize(out_b)} bytes)")

# 验证成品文档
print("\n[7] 验证成品文档格式...")
for label, out_path in [("方式A", out_a), ("方式B", out_b)]:
    print(f"\n  --- {label} 成品文档 ---")
    v = parse_document(out_path)
    print(f"  段落数: {len(v.paragraphs)}")
    print(f"  表格数: {len(v.tables)}")
    print(f"  页面: {v.page_width}x{v.page_height}pt")
    print(f"  页边距: T={v.margin_top} B={v.margin_bottom} L={v.margin_left} R={v.margin_right}")
    print(f"  页眉: '{v.header}'")

    for p in v.paragraphs:
        east = p.font.font_name_east_asia or "?"
        name = p.font.font_name or "?"
        sz = p.font.font_size or "?"
        bold = p.font.bold
        a = p.paragraph.alignment or "?"
        ls = p.paragraph.line_spacing or "?"
        ind = p.paragraph.first_line_indent or "?"
        t = p.text[:35] + "..." if len(p.text) > 35 else p.text
        print(f"  [{p.style_name}] {east}/{name} {sz}pt bold={bold} a={a} ls={ls} ind={ind} | {t}")

    if v.tables:
        t = v.tables[0]
        print(f"  表格: {t.rows}x{t.cols}")
        for i, row in enumerate(t.cells):
            print(f"    Row {i}: {row}")

# 格式检查
print("\n[8] 格式检查汇总...")
for label, out_path in [("A", out_a), ("B", out_b)]:
    v = parse_document(out_path)
    checks = []

    # 标题检查
    title_ok = False
    for p in v.paragraphs:
        if "人工智能在日常" in p.text:
            east = p.font.font_name_east_asia
            sz = p.font.font_size
            bold = p.font.bold
            align = p.paragraph.alignment
            title_ok = east == "黑体" and sz == 22.0 and bold == True and align == "center"
            checks.append(("标题=黑体22pt加粗居中", title_ok, f"east={east} sz={sz} bold={bold} align={align}"))
            break

    # H1检查
    h1_ok = False
    for p in v.paragraphs:
        if p.text.strip() == "引言":
            h1_ok = p.font.font_name_east_asia == "黑体" and p.font.font_size == 16.0
            checks.append(("H1(引言)=黑体16pt", h1_ok, f"east={p.font.font_name_east_asia} sz={p.font.font_size}"))
            break

    # H2检查
    h2_ok = False
    for p in v.paragraphs:
        if "智能音箱" in p.text:
            h2_ok = p.font.font_name_east_asia == "黑体" and p.font.font_size == 14.0
            checks.append(("H2(智能音箱)=黑体14pt", h2_ok, f"east={p.font.font_name_east_asia} sz={p.font.font_size}"))
            break

    # 正文检查
    body_ok = False
    for p in v.paragraphs:
        if "深入到我们日常" in p.text:
            body_ok = p.font.font_name_east_asia == "宋体" and p.font.font_size == 12.0 and p.paragraph.alignment == "justify"
            checks.append(("正文=宋体12pt两端对齐", body_ok, f"east={p.font.font_name_east_asia} sz={p.font.font_size} a={p.paragraph.alignment}"))
            break

    # 表格检查
    table_ok = False
    if v.tables:
        cells = v.tables[0].cells
        if len(cells) >= 3 and "应用领域" in cells[0]:
            table_ok = True
    checks.append(("表格=应用领域(不乱码)", table_ok, ""))

    # 页眉检查
    header_ok = v.header == "人工智能应用研究"
    checks.append(("页眉正确", header_ok, f"header='{v.header}'"))

    print(f"\n  方式{label}:")
    for name, ok, detail in checks:
        print(f"    {'✅' if ok else '❌'} {name}" + (f" — {detail}" if detail and not ok else ""))

print("\n" + "=" * 70)
print("  新内容端到端测试完成!")
print("=" * 70)
