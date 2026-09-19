"""Test all 4 preset templates against national standards."""
import requests, json

API = "http://localhost:8000/api"
PASS = 0
FAIL = 0

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        print(f"  ✅ {name}")
        PASS += 1
    else:
        print(f"  ❌ {name} — {detail}")
        FAIL += 1

r = requests.get(f"{API}/rules/presets")
presets = r.json()["presets"]
print(f"预设模板数: {len(presets)}")
for p in presets:
    print(f'  {p["id"]}: {p["name"]} — {p.get("description", "")[:60]}')

check("有4套预设", len(presets) == 4)
check("包含博士论文", any(p["id"] == "doctoral_thesis" for p in presets))

for preset_id, expected_name in [
    ("undergraduate_thesis", "本科毕业论文"),
    ("master_thesis", "硕士学位论文"),
    ("doctoral_thesis", "博士学位论文"),
    ("journal_article", "期刊投稿"),
]:
    print(f"\n--- {expected_name} ---")
    r = requests.post(f"{API}/rules/from-preset", data={"preset_id": preset_id})
    if r.status_code != 200:
        check(f"{expected_name} 返回200", False, r.text[:100])
        continue
    data = r.json()
    rules = data["rule_set"]
    styles = rules.get("styles", {})
    doc = rules.get("document_level", {})

    check(f"{expected_name} 返回200", r.status_code == 200)

    if preset_id == "undergraduate_thesis":
        check("本科: 页边距左=3cm(85pt)", abs(doc["margin_left"] - 85.05) < 1, str(doc["margin_left"]))
        check("本科: 页边距右=2cm(57pt)", abs(doc["margin_right"] - 56.69) < 1, str(doc["margin_right"]))
        check("本科: Title=二号(22pt)", styles["Title"]["font"]["font_size"] == 22.0)
        check("本科: Body=小四(12pt)", styles["Body"]["font"]["font_size"] == 12.0)
        check("本科: Body行距=1.5倍", styles["Body"]["paragraph"]["line_spacing"] == 1.5)
        check("本科: Reference=五号(10.5pt)", styles["Reference"]["font"]["font_size"] == 10.5)
        check("本科: H1=三号(16pt)", styles["Heading1"]["font"]["font_size"] == 16.0)
        check("本科: H2=四号(14pt)", styles["Heading2"]["font"]["font_size"] == 14.0)
        check("本科: 标题编号=中文", rules["heading_numbering"]["format"] == "chinese")

    if preset_id == "master_thesis":
        check("硕士: Title=小二(18pt)", styles["Title"]["font"]["font_size"] == 18.0)
        check("硕士: Body行距=固定20磅", styles["Body"]["paragraph"]["line_spacing"] == 20.0)
        check("硕士: Body行距规则=exact", styles["Body"]["paragraph"]["line_spacing_rule"] == "exact")
        check("硕士: 页边距天头=2.5cm", abs(doc["margin_top"] - 70.88) < 1)
        check("硕士: 页边距地角=2cm", abs(doc["margin_bottom"] - 56.69) < 1)
        check("硕士: Reference=五号(10.5pt)", styles["Reference"]["font"]["font_size"] == 10.5)
        check("硕士: 页眉=硕士学位论文", doc.get("header") == "硕士学位论文")

    if preset_id == "doctoral_thesis":
        check("博士: Title=二号(22pt)", styles["Title"]["font"]["font_size"] == 22.0)
        check("博士: Body行距=固定22磅", styles["Body"]["paragraph"]["line_spacing"] == 22.0)
        check("博士: 页眉=博士学位论文", doc.get("header") == "博士学位论文")

    if preset_id == "journal_article":
        check("期刊: 页边距=2.5cm四周", abs(doc["margin_top"] - 70.88) < 1)
        check("期刊: Body=五号(10.5pt)", styles["Body"]["font"]["font_size"] == 10.5)
        check("期刊: Body行距=单倍", styles["Body"]["paragraph"]["line_spacing"] == 1.0)
        check("期刊: Reference=小五(9pt)", styles["Reference"]["font"]["font_size"] == 9.0)
        check("期刊: Title=三号(16pt)", styles["Title"]["font"]["font_size"] == 16.0)

print(f"\n{'=' * 60}")
print(f"  测试结果: 通过={PASS} 失败={FAIL} 总计={PASS+FAIL}")
print(f"{'=' * 60}")
