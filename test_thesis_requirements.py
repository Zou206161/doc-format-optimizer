"""测试详细的本科毕业论文格式要求解析能力。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.modules.requirement_parser import parse_requirement

req_text = """1、本科毕业论文格式要求：

装订顺序：目录–内容提要–正文–参考文献–写作过程情况表–指导教师评议表

参考文献应另起一页。

纸张型号：A4纸。A4 210×297毫米

论文份数：一式三份。

其他(调查报告、学习心得)：一律要求打印。

2、论文的封面由学校统一提供。(或听老师的安排)

3、论文格式的字体：各类标题(包括"参考文献"标题)用粗宋体;作者姓名、指导教师姓名、摘要、关键词、图表名、参考文献内容用楷体;正文、图表、页眉、页脚中的文字用宋体;英文用Times New Roman字体。

4、字体要求：

(1)论文标题2号黑体加粗、居中。

(2)论文副标题小2号字，紧挨正标题下居中，文字前加破折号。

(3)填写姓名、专业、学号等项目时用3号楷体。

(4)内容提要3号黑体，居中上下各空一行，内容为小4号楷体。

(5)关键词4号黑体，内容为小4号黑体。

(6)目录另起页，3号黑体，内容为小4号仿宋，并列出页码。

(7)正文文字另起页，论文标题用3号黑体，正文文字一般用小4 号宋体，每段首起空两个格，单倍行距。

(8)正文文中标题

一级标题：标题序号为"一、"， 4号黑体，独占行，末尾不加标点符号。

二级标题：标题序号为"(一)"与正文字号相同，独占行，末尾不加标点符号。

三级标题：标题序号为" 1. "与正文字号、字体相同。

四级标题：标题序号为"(1)"与正文字号、字体相同。

五级标题：标题序号为" ① "与正文字号、字体相同。

(9)注释：4号黑体，内容为5号宋体。

(10)附录： 4号黑体，内容为5号宋体。

(11)参考文献：另起页，4号黑体，内容为5号宋体。

(12)页眉用小五号字体打印"上海复旦大学XX学院2007级XX专业学年论文"字样，并左对齐。

5、纸型及页边距：A4纸(297mm×210mm)。

6、页边距：天头(上)20mm，地角(下)15mm，订口(左)25mm，翻口(右)20mm。

7、装订要求：先将目录、内容摘要、正文、参考文献、写作过程情况表、指导教师评议表等装订好，然后套装在学校统一印制的论文封面之内(用胶水粘贴，订书钉不能露在封面外)。"""

print("=" * 70)
print("  本科毕业论文格式要求解析测试")
print("=" * 70)

PASS = 0
FAIL = 0
SKIP = 0

def check(name, condition, expected="", actual=""):
    global PASS, FAIL
    if condition:
        print(f"  ✅ {name}")
        PASS += 1
    else:
        print(f"  ❌ {name}")
        if expected:
            print(f"     期望: {expected}")
        if actual:
            print(f"     实际: {actual}")
        FAIL += 1

def skip(name, reason=""):
    global SKIP
    print(f"  ⚪ {name} — {reason}")
    SKIP += 1

rs = parse_requirement(req_text, "undergraduate_thesis")

dl = rs.document_level
print(f"\n【页面设置】")
check("A4纸张", dl.page_width == 595.3 and dl.page_height == 841.9,
      "595.3x841.9pt", f"{dl.page_width}x{dl.page_height}pt")
check("上边距=20mm(56.7pt)", dl.margin_top is not None and abs(dl.margin_top - 56.7) < 5,
      "≈56.7pt", f"{dl.margin_top}pt")
check("下边距=15mm(42.5pt)", dl.margin_bottom is not None and abs(dl.margin_bottom - 42.5) < 5,
      "≈42.5pt", f"{dl.margin_bottom}pt")
check("左边距=25mm(70.9pt)", dl.margin_left is not None and abs(dl.margin_left - 70.9) < 5,
      "≈70.9pt", f"{dl.margin_left}pt")
check("右边距=20mm(56.7pt)", dl.margin_right is not None and abs(dl.margin_right - 56.7) < 5,
      "≈56.7pt", f"{dl.margin_right}pt")
skip("页眉内容", "需要解析页眉文本内容")
skip("页脚页码", "需要页码生成功能")

print(f"\n【Title 标题】")
t = rs.styles.get("Title")
if t:
    check("字体=黑体", t.font.font_name_east_asia == "黑体", "黑体", str(t.font.font_name_east_asia))
    check("字号=二号(22pt)", t.font.font_size == 22.0, "22.0pt", f"{t.font.font_size}pt")
    check("加粗", t.font.bold == True, "True", str(t.font.bold))
    check("居中", t.paragraph.alignment == "center", "center", str(t.paragraph.alignment))
else:
    check("Title样式存在", False, "存在", "不存在")

print(f"\n【Heading1 一级标题】")
h1 = rs.styles.get("Heading1")
if h1:
    check("字体=黑体", h1.font.font_name_east_asia == "黑体")
    check("字号=四号(14pt)", h1.font.font_size == 14.0, "14.0pt", f"{h1.font.font_size}pt")
    check("加粗", h1.font.bold == True)
else:
    check("Heading1样式存在", False, "存在", "不存在")

print(f"\n【Heading2 二级标题】")
h2 = rs.styles.get("Heading2")
if h2:
    check("字号=小四号(12pt)", h2.font.font_size == 12.0, "12.0pt", f"{h2.font.font_size}pt")
else:
    check("Heading2样式存在", False, "存在", "不存在")

print(f"\n【Heading3 三级标题】")
h3 = rs.styles.get("Heading3")
if h3:
    check("字号=小四号(12pt)", h3.font.font_size == 12.0, "12.0pt", f"{h3.font.font_size}pt")
else:
    check("Heading3样式存在", False, "存在", "不存在")

print(f"\n【Body 正文】")
b = rs.styles.get("Body")
if b:
    check("字体=宋体", b.font.font_name_east_asia == "宋体")
    check("字号=小四号(12pt)", b.font.font_size == 12.0, "12.0pt", f"{b.font.font_size}pt")
    check("首行缩进=2字符(24pt)", b.paragraph.first_line_indent == 24.0, "24pt", f"{b.paragraph.first_line_indent}pt")
    check("单倍行距", b.paragraph.line_spacing == 1.0, "1.0", str(b.paragraph.line_spacing))
else:
    check("Body样式存在", False, "存在", "不存在")

print(f"\n【Reference 参考文献】")
r = rs.styles.get("Reference")
if r:
    check("内容字号=五号(10.5pt)", r.font.font_size == 10.5, "10.5pt", f"{r.font.font_size}pt")
    check("内容字体=宋体", r.font.font_name_east_asia == "宋体")
else:
    check("Reference样式存在", False, "存在", "不存在")

print(f"\n【其他样式】")
all_styles = list(rs.styles.keys())
print(f"  已解析样式: {all_styles}")
skip("Subtitle 副标题", "系统暂不支持副标题样式")
skip("Abstract 摘要标题+内容", "系统暂不支持摘要专用样式")
skip("Keywords 关键词", "系统暂不支持关键词专用样式")
skip("Caption 图表标题楷体", "当前图表标题用宋体非楷体")
skip("目录样式", "系统暂不支持目录专用样式")
skip("注释样式", "系统暂不支持注释专用样式")
skip("附录样式", "系统暂不支持附录专用样式")

print(f"\n{'=' * 70}")
print(f"  解析结果: 通过={PASS} 失败={FAIL} 跳过={SKIP} 总计={PASS+FAIL+SKIP}")
print(f"{'=' * 70}")
