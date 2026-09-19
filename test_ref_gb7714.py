"""测试参考文献 GB/T 7714 标准化效果。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.modules.reference_normalizer import normalize_reference, _looks_like_reference

print("=" * 70)
print("  参考文献 GB/T 7714-2015 标准化测试")
print("=" * 70)

test_cases = [
    # Chinese journal articles
    "王立军，李华. 人工智能医疗应用的法律规制研究. 中国法学，2024，42(3): 55-72.",
    "陈敏，赵强，刘洋. 深度学习在医学影像中的公平性评估. 计算机学报，2023，46(7): 1432-1445.",
    # Chinese monograph
    "世界卫生组织. 人工智能在健康领域的伦理与治理指南. 日内瓦: 世界卫生组织出版社，2023.",
    # English journal articles
    "Smith J, Johnson K. Accountability and AI in clinical decision-making. Journal of Medical Ethics, 2023, 49(2): 110-118.",
    "Zhang L, Wang H. Federated learning for medical imaging privacy preservation. IEEE Transactions on Medical Imaging, 2024, 43(1): 89-101.",
    # Mixed/edge cases
    "张三, 李四, 王五, 赵六. 基于深度学习的图像识别研究. 电子学报, 2022, 50(12): 2800-2810.",
]

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

for i, raw in enumerate(test_cases):
    result = normalize_reference(raw, i)
    print(f"\n【{i+1}】{raw[:60]}")
    print(f"     → {result.optimized_text[:80]}")

    # Basic checks
    check("非空文本", result.optimized_text.strip() != "")
    check("包含文献类型标识[J]/[M]/[C]等",
          "[J]" in result.optimized_text or "[M]" in result.optimized_text or
          "[C]" in result.optimized_text or "[D]" in result.optimized_text,
          f"结果: {result.optimized_text[:80]}")
    check("以英文句点结尾", result.optimized_text.rstrip().endswith("."))

    if result.changes:
        print(f"     修改数: {len(result.changes)}")
        for ch in result.changes[:2]:
            print(f"       - {ch.explanation[:50]}")

print(f"\n{'=' * 70}")
print(f"  参考文献标准化测试: 通过={PASS} 失败={FAIL} 总计={PASS+FAIL}")
print(f"{'=' * 70}")
