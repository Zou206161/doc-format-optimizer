"""端到端测试：用户真实文档 + 参考文献 GB/T 7714 标准化。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.modules.parser import parse_document
from src.modules.content_optimizer import optimize_content
from src.modules.requirement_parser import parse_requirement
from src.modules.format_applier import apply_format
from src.modules.doc_generator import generate_document

BASE = os.path.dirname(os.path.abspath(__file__))
USER_DOC = os.path.join(BASE, "user_real_doc.docx")

USER_REQUIREMENTS = """学术论文格式规范要求如下：
纸张规格使用A4纸张。
页边距要求上边距二点五厘米，下边距二点五厘米，左边距三厘米，右边距二点五厘米。
中文字体正文使用宋体，大标题使用黑体。
英文字体和数字使用Times New Roman字体。
字号标准规定大标题使用二号字，一级标题使用三号字，二级标题使用四号字，三级标题使用小四号字，正文内容使用小四号字，图表标题使用五号字。
段落格式要求正文段落首行缩进两个汉字字符。
全文行距设定为固定值二十磅，段前段后间距均调整为零。
标题位置要求论文大标题居中对齐，一级标题顶格，二级标题缩进两个字符，三级标题缩进四个字符。
图表规范要求图表需居中放置，图名置于图下方，表名置于表上方，均使用五号字，图表编号采用阿拉伯数字连续编号，例如图一、表一。
参考文献著录采用GB/T7714格式，正文中的引用处以数字上标标注序号，例如一，文末参考文献列表按照引用顺序排列。"""

print("=" * 70)
print("  端到端测试：参考文献 GB/T 7714 标准化")
print("=" * 70)

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

# 1. Parse
doc_obj = parse_document(USER_DOC)
print(f"\n【1】文档解析: {len(doc_obj.paragraphs)}段, {len(doc_obj.tables)}表")

# 2. Optimize content (includes reference normalization)
opt_result = optimize_content(doc_obj)
print(f"\n【2】内容优化: {opt_result.total_changes} 处修改")
print(f"     修改类型: {opt_result.by_type}")

# Find reference changes
ref_changes = [p for p in opt_result.paragraphs if p.changes and p.index > 30]
print(f"\n     参考文献段修改数: {len(ref_changes)}")
for r in ref_changes:
    print(f"       [{r.index}] 原文: {r.original_text[:50]}")
    print(f"            优化: {r.optimized_text[:50]}")
    for ch in r.changes:
        print(f"              → {ch.explanation[:50]}")

# 3. Parse requirements
rule_set = parse_requirement(USER_REQUIREMENTS)
print(f"\n【3】格式规则: {list(rule_set.styles.keys())}")

# 4. Apply format
formatted = apply_format(doc_obj, opt_result, rule_set)
style_counts = {}
for fp in formatted.paragraphs:
    style_counts[fp.style_key] = style_counts.get(fp.style_key, 0) + 1
print(f"\n【4】格式套用: 样式分布 {style_counts}")

# 5. Generate
out_path = os.path.join(BASE, "user_final_with_refs.docx")
generate_document(formatted, out_path)
print(f"\n【5】文档生成: {out_path} ({os.path.getsize(out_path)} bytes)")

# 6. Verify references in output
v = parse_document(out_path)
ref_start = None
ref_items = []
for i, p in enumerate(v.paragraphs):
    if p.text.strip() == "参考文献":
        ref_start = i
        continue
    if ref_start is not None and p.text.strip():
        ref_items.append((i, p))

print(f"\n【6】成品参考文献验证: {len(ref_items)} 条")
for idx, (i, p) in enumerate(ref_items):
    text = p.text.strip()
    has_type = "[J]" in text or "[M]" in text or "[C]" in text or "[D]" in text
    ends_dot = text.endswith(".")
    print(f"  [{idx+1}] {text[:60]}")
    check(f"文献{idx+1}: 有类型标识", has_type)
    check(f"文献{idx+1}: 以英文句点结尾", ends_dot)
    check(f"文献{idx+1}: 五号字(10.5pt)", p.font.font_size == 10.5,
          f"期望10.5pt，实际{p.font.font_size}pt")
    check(f"文献{idx+1}: 宋体", p.font.font_name_east_asia == "宋体",
          f"期望宋体，实际{p.font.font_name_east_asia}")
    check(f"文献{idx+1}: 左缩进24pt(悬挂)", p.paragraph.left_indent == 24.0,
          f"期望24pt，实际{p.paragraph.left_indent}pt")
    check(f"文献{idx+1}: 无首行缩进",
          p.paragraph.first_line_indent is None or p.paragraph.first_line_indent == 0,
          f"实际{p.paragraph.first_line_indent}pt")

print(f"\n{'=' * 70}")
print(f"  端到端测试结果: 通过={PASS} 失败={FAIL} 总计={PASS+FAIL}")
print(f"{'=' * 70}")
