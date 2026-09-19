"""检查参考文献格式是否符合规范。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.modules.parser import parse_document

doc = parse_document("user_final_output.docx")

print("=" * 70)
print("  参考文献格式合规性检查")
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
        if expected:
            print(f"     期望: {expected}")
        if actual:
            print(f"     实际: {actual}")
        FAIL += 1

# 找参考文献标题
ref_heading_idx = None
ref_heading = None
for i, p in enumerate(doc.paragraphs):
    if p.text.strip() == "参考文献":
        ref_heading_idx = i
        ref_heading = p
        break

print("\n【1. 参考文献标题】")
if ref_heading:
    check("标题文本正确", ref_heading.text.strip() == "参考文献")
    check("黑体", ref_heading.font.font_name_east_asia == "黑体",
          "黑体", str(ref_heading.font.font_name_east_asia))
    check("三号(16pt)", ref_heading.font.font_size == 16.0,
          "16.0pt", f"{ref_heading.font.font_size}pt")
    check("加粗", ref_heading.font.bold == True,
          "True", str(ref_heading.font.bold))
    check("顶格(首行缩进=0)",
          ref_heading.paragraph.first_line_indent == 0.0 or ref_heading.paragraph.first_line_indent is None,
          "0pt", str(ref_heading.paragraph.first_line_indent))
else:
    check("找到参考文献标题", False, "存在", "未找到")

# 找参考文献条目
ref_items = []
if ref_heading_idx is not None:
    for i in range(ref_heading_idx + 1, len(doc.paragraphs)):
        p = doc.paragraphs[i]
        if p.text.strip():
            ref_items.append((i, p))

print(f"\n【2. 参考文献条目】共 {len(ref_items)} 条")

if ref_items:
    # 检查第一条
    idx, first = ref_items[0]
    print(f"\n  第一条: {first.text[:50]}...")
    check("字号=五号(10.5pt)", first.font.font_size == 10.5,
          "10.5pt", f"{first.font.font_size}pt")
    check("中文字体=宋体", first.font.font_name_east_asia == "宋体",
          "宋体", str(first.font.font_name_east_asia))
    check("西文字体=Times New Roman", first.font.font_name == "Times New Roman",
          "Times New Roman", str(first.font.font_name))
    check("无首行缩进", first.paragraph.first_line_indent is None or first.paragraph.first_line_indent == 0,
          "None/0", str(first.paragraph.first_line_indent))
    check("左缩进=24pt(悬挂缩进)", first.paragraph.left_indent == 24.0,
          "24.0pt", str(first.paragraph.left_indent))
    check("两端对齐", str(first.paragraph.alignment).lower() == "alignment.justify" or first.paragraph.alignment == "justify",
          "justify", str(first.paragraph.alignment))

    # 检查所有条目的一致性
    print(f"\n  一致性检查:")
    sizes = [p.font.font_size for _, p in ref_items]
    east_fonts = [p.font.font_name_east_asia for _, p in ref_items]
    left_indents = [p.paragraph.left_indent for _, p in ref_items]
    first_indents = [p.paragraph.first_line_indent for _, p in ref_items]

    check("所有条目字号一致", len(set(sizes)) == 1, f"统一 {sizes[0]}", str(set(sizes)))
    check("所有条目中文字体一致", len(set(east_fonts)) == 1, f"统一 {east_fonts[0]}", str(set(east_fonts)))
    check("所有条目左缩进一致", len(set(left_indents)) == 1, f"统一 {left_indents[0]}", str(set(left_indents)))

    # 检查条目内容
    print(f"\n  条目内容预览:")
    for i, (idx, p) in enumerate(ref_items):
        print(f"    [{i+1}] {p.text[:55]}")

print(f"\n{'=' * 70}")
print(f"  参考文献检查结果: 通过={PASS} 失败={FAIL}")
print(f"{'=' * 70}")
