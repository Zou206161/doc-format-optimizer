"""Text requirement parser — converts natural-language format descriptions into a
FormatRuleSet via LLM (Method B)."""

from __future__ import annotations

import logging
import re
from typing import Any

from src.models import (
    Alignment,
    DocumentLevel,
    FontFormat,
    FormatRuleSet,
    HeadingNumbering,
    ParagraphFormat,
    StyleFormat,
)
from src.modules.llm_client import llm_client
from src.modules.preset_templates import get_preset_by_id, match_preset
from src.utils.font_size_map import CHINESE_FONT_SIZE_MAP, PT_PER_CM

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = f"""你是一位文档格式规范解析专家。请将用户给出的格式要求文本解析为结构化的 JSON 格式规则集。

中文字号到磅值(pt)映射表：
{", ".join(f"{k}={v}" for k, v in CHINESE_FONT_SIZE_MAP.items())}

单位换算规则：
- 1cm ≈ {PT_PER_CM}pt
- 1字符宽度 = 当前字号磅值（如小四12pt，2字符缩进=24pt）
- 行距倍数（如1.5倍）用浮点数表示；固定行距（如固定值20pt）直接用pt数值

对齐方式取值：left, center, right, justify

请返回 JSON，结构如下（文本未提及的字段填 null）：
{{
  "document_level": {{
    "page_width": float|null, "page_height": float|null,
    "margin_top": float|null, "margin_bottom": float|null,
    "margin_left": float|null, "margin_right": float|null,
    "header": string|null, "footer": string|null,
    "default_font_name": string|null, "default_font_name_east_asia": string|null, "default_font_size": float|null
  }},
  "styles": {{
    "Title": {{"font_name": ..., "font_name_east_asia": ..., "font_size": ..., "bold": ..., "alignment": ..., "space_before": ..., "space_after": ...}},
    "Heading1": {{...same...}},
    "Heading2": {{...same...}},
    "Heading3": {{...same...}},
    "Body": {{...same..., "line_spacing": ..., "first_line_indent": ...}},
    "Caption": {{...same...}},
    "Reference": {{...same...}}
  }},
  "heading_numbering": {{"format": "decimal"|"chinese"|"upper_letter"|"lower_letter"|null, "separator": string|null, "levels": int|null}}
}}

注意：
- 只填文本明确提到的字段，其余全部填 null
- 中文字号（如"小四"）需转换为对应磅值
- cm 和字符需转换为 pt
- 字体名称直接使用中文名（如"宋体"、"黑体"）
- bold 为 true/false/null
"""

_ACADEMIC_DEFAULTS = FormatRuleSet(
    document_level=DocumentLevel(
        page_width=595.3,
        page_height=841.9,
        margin_top=72.0,
        margin_bottom=72.0,
        margin_left=90.0,
        margin_right=90.0,
        default_font=FontFormat(font_name="Times New Roman", font_name_east_asia="宋体", font_size=12.0),
    ),
    styles={
        "Body": StyleFormat(
            font=FontFormat(font_name="Times New Roman", font_name_east_asia="宋体", font_size=12.0),
            paragraph=ParagraphFormat(
                alignment=Alignment.JUSTIFY, line_spacing=1.5, first_line_indent=24.0
            ),
        )
    },
    heading_numbering=HeadingNumbering(),
)


def _coerce_alignment(val: Any) -> Alignment | None:
    if val is None:
        return None
    s = str(val).strip().lower()
    mapping = {
        "left": Alignment.LEFT,
        "左对齐": Alignment.LEFT,
        "左": Alignment.LEFT,
        "center": Alignment.CENTER,
        "居中": Alignment.CENTER,
        "居中对齐": Alignment.CENTER,
        "right": Alignment.RIGHT,
        "右对齐": Alignment.RIGHT,
        "右": Alignment.RIGHT,
        "justify": Alignment.JUSTIFY,
        "两端对齐": Alignment.JUSTIFY,
        "两对齐": Alignment.JUSTIFY,
    }
    return mapping.get(s)


def _build_font(data: dict) -> FontFormat:
    return FontFormat(
        font_name=data.get("font_name"),
        font_name_east_asia=data.get("font_name_east_asia") or data.get("font_name"),
        font_size=data.get("font_size"),
        bold=data.get("bold"),
    )


def _build_para_fmt(data: dict) -> ParagraphFormat:
    return ParagraphFormat(
        alignment=_coerce_alignment(data.get("alignment")),
        line_spacing=data.get("line_spacing"),
        space_before=data.get("space_before"),
        space_after=data.get("space_after"),
        first_line_indent=data.get("first_line_indent"),
    )


def _build_style(data: dict) -> StyleFormat:
    return StyleFormat(font=_build_font(data), paragraph=_build_para_fmt(data))


def _build_doc_level(data: dict) -> DocumentLevel:
    dl = DocumentLevel(
        page_width=data.get("page_width"),
        page_height=data.get("page_height"),
        margin_top=data.get("margin_top"),
        margin_bottom=data.get("margin_bottom"),
        margin_left=data.get("margin_left"),
        margin_right=data.get("margin_right"),
        header=data.get("header"),
        footer=data.get("footer"),
    )
    df = data.get("default_font_name") or data.get("default_font_name_east_asia")
    if df or data.get("default_font_size"):
        dl.default_font = FontFormat(
            font_name=data.get("default_font_name"),
            font_name_east_asia=data.get("default_font_name_east_asia") or data.get("default_font_name"),
            font_size=data.get("default_font_size"),
        )
    return dl


def _parse_llm_response(data: dict) -> FormatRuleSet:
    """Convert the LLM's JSON dict into a FormatRuleSet (nulls preserved)."""
    rule_set = FormatRuleSet(
        document_level=_build_doc_level(data.get("document_level", {})),
    )
    for style_name, style_data in (data.get("styles") or {}).items():
        rule_set.styles[style_name] = _build_style(style_data)

    hn = data.get("heading_numbering") or {}
    rule_set.heading_numbering = HeadingNumbering(
        format=hn.get("format", "decimal"),
        separator=hn.get("separator", "."),
        levels=hn.get("levels", 3) or 3,
    )
    return rule_set


def _merge_into(base: FormatRuleSet, override: FormatRuleSet, source: str) -> FormatRuleSet:
    """Deep-merge *override* into *base*: non-null fields from override win."""

    def merge_font(b: FontFormat, o: FontFormat) -> FontFormat:
        return FontFormat(
            font_name=o.font_name if o.font_name else b.font_name,
            font_name_east_asia=o.font_name_east_asia if o.font_name_east_asia else b.font_name_east_asia,
            font_size=o.font_size if o.font_size is not None else b.font_size,
            bold=o.bold if o.bold is not None else b.bold,
            italic=o.italic if o.italic is not None else b.italic,
            underline=o.underline if o.underline is not None else b.underline,
            color=o.color if o.color else b.color,
        )

    def merge_para(b: ParagraphFormat, o: ParagraphFormat) -> ParagraphFormat:
        return ParagraphFormat(
            alignment=o.alignment if o.alignment else b.alignment,
            line_spacing=o.line_spacing if o.line_spacing is not None else b.line_spacing,
            line_spacing_rule=o.line_spacing_rule if o.line_spacing_rule else b.line_spacing_rule,
            space_before=o.space_before if o.space_before is not None else b.space_before,
            space_after=o.space_after if o.space_after is not None else b.space_after,
            first_line_indent=o.first_line_indent if o.first_line_indent is not None else b.first_line_indent,
            left_indent=o.left_indent if o.left_indent is not None else b.left_indent,
            right_indent=o.right_indent if o.right_indent is not None else b.right_indent,
        )

    b_dl = base.document_level
    o_dl = override.document_level
    base.document_level = DocumentLevel(
        page_width=o_dl.page_width if o_dl.page_width else b_dl.page_width,
        page_height=o_dl.page_height if o_dl.page_height else b_dl.page_height,
        margin_top=o_dl.margin_top if o_dl.margin_top is not None else b_dl.margin_top,
        margin_bottom=o_dl.margin_bottom if o_dl.margin_bottom is not None else b_dl.margin_bottom,
        margin_left=o_dl.margin_left if o_dl.margin_left is not None else b_dl.margin_left,
        margin_right=o_dl.margin_right if o_dl.margin_right is not None else b_dl.margin_right,
        header=o_dl.header if o_dl.header else b_dl.header,
        footer=o_dl.footer if o_dl.footer else b_dl.footer,
        default_font=merge_font(b_dl.default_font, o_dl.default_font),
    )

    all_keys = set(base.styles.keys()) | set(override.styles.keys())
    for key in all_keys:
        b_style = base.styles.get(key, StyleFormat())
        o_style = override.styles.get(key, StyleFormat())
        base.styles[key] = StyleFormat(
            font=merge_font(b_style.font, o_style.font),
            paragraph=merge_para(b_style.paragraph, o_style.paragraph),
        )

    return base


def _record_sources(
    rule_set: FormatRuleSet,
    parsed: FormatRuleSet | None,
    preset_rs: FormatRuleSet | None,
) -> None:
    """Populate the sources dict to indicate where each value came from."""
    sources: dict[str, str] = {}

    def track_font(prefix: str, base_f: FontFormat, parsed_f: FontFormat | None, preset_f: FontFormat | None):
        for attr in ("font_name", "font_name_east_asia", "font_size", "bold"):
            b_val = getattr(base_f, attr)
            p_val = getattr(parsed_f, attr) if parsed_f else None
            key = f"{prefix}.{attr}"
            if p_val is not None and p_val != b_val:
                sources[key] = "text_parse"
            elif preset_f and getattr(preset_f, attr) is not None:
                sources[key] = "preset"
            elif b_val is not None:
                sources[key] = "default"

    def track_para(prefix: str, base_p: ParagraphFormat, parsed_p: ParagraphFormat | None, preset_p: ParagraphFormat | None):
        for attr in ("alignment", "line_spacing", "space_before", "space_after", "first_line_indent"):
            b_val = getattr(base_p, attr)
            p_val = getattr(parsed_p, attr) if parsed_p else None
            key = f"{prefix}.{attr}"
            if p_val is not None and p_val != b_val:
                sources[key] = "text_parse"
            elif preset_p and getattr(preset_p, attr) is not None:
                sources[key] = "preset"
            elif b_val is not None:
                sources[key] = "default"

    dl_base = _ACADEMIC_DEFAULTS.document_level
    dl_parsed = parsed.document_level if parsed else None
    dl_preset = preset_rs.document_level if preset_rs else None
    track_font("document_level.default_font", dl_base.default_font,
               dl_parsed.default_font if dl_parsed else None,
               dl_preset.default_font if dl_preset else None)
    for attr in ("page_width", "page_height", "margin_top", "margin_bottom", "margin_left", "margin_right", "header", "footer"):
        key = f"document_level.{attr}"
        p_val = getattr(dl_parsed, attr) if dl_parsed else None
        b_val = getattr(dl_base, attr)
        ps_val = getattr(dl_preset, attr) if dl_preset else None
        if p_val is not None and p_val != b_val:
            sources[key] = "text_parse"
        elif ps_val is not None:
            sources[key] = "preset"
        elif b_val is not None:
            sources[key] = "default"

    for style_name, style in rule_set.styles.items():
        parsed_style = parsed.styles.get(style_name) if parsed else None
        preset_style = preset_rs.styles.get(style_name) if preset_rs else None
        track_font(f"styles.{style_name}.font", style.font,
                   parsed_style.font if parsed_style else None,
                   preset_style.font if preset_style else None)
        track_para(f"styles.{style_name}.paragraph", style.paragraph,
                   parsed_style.paragraph if parsed_style else None,
                   preset_style.paragraph if preset_style else None)

    rule_set.sources = sources


def _parse_cn_number(text: str) -> float | None:
    """Parse Chinese number expressions like 二点五, 三, 十, 二十."""
    cn_map = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
              "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    text = text.strip()
    if not text:
        return None
    if text.isdigit():
        return float(text)
    if "点" in text or "．" in text:
        parts = re.split(r"[点．]", text)
        int_part = 0.0
        frac_part = 0.0
        if parts[0] and parts[0] in cn_map:
            int_part = float(cn_map[parts[0]])
        if len(parts) > 1 and parts[1] and parts[1] in cn_map:
            frac_part = cn_map[parts[1]] * 0.1
        return int_part + frac_part if int_part or frac_part else None
    if text in cn_map:
        return float(cn_map[text])
    if text.startswith("十"):
        rest = text[1:]
        return 10.0 + float(cn_map[rest]) if rest and rest in cn_map else 10.0
    if text.startswith("二十"):
        rest = text[2:]
        return 20.0 + float(cn_map[rest]) if rest and rest in cn_map else 20.0
    try:
        return float(text)
    except ValueError:
        return None


def _extract_cm(text: str, key_patterns: list[str]) -> float | None:
    """Extract a cm measurement for a given key pattern. Returns pt value.
    
    Supports both cm and mm units. Returns the LAST match (most recent spec wins).
    """
    best = None
    for pattern in key_patterns:
        # Try cm first
        for m in re.finditer(pattern + r"([\d点二两三四五六七八九十〇．\.]+)\s*(?:厘米|cm|毫米|mm)", text):
            val = _parse_cn_number(m.group(1))
            if val is not None:
                unit = m.group(0)[-2:] if len(m.group(0)) >= 2 else ""
                if "mm" in unit or "毫米" in unit:
                    val = val / 10.0  # mm → cm
                best = round(val * PT_PER_CM, 2)
    return best


def _extract_pt(text: str, key_patterns: list[str]) -> float | None:
    """Extract a pt/磅 measurement for a given key pattern."""
    for pattern in key_patterns:
        m = re.search(pattern + r"([\d点二两三四五六七八九十〇．\.]+)\s*磅", text)
        if m:
            val = _parse_cn_number(m.group(1))
            if val is not None:
                return val
    return None


def _extract_font_size(text: str, key_patterns: list[str]) -> float | None:
    """Extract font size for a key pattern. First match wins (earliest, most prominent spec).

    Searches within 35 chars after each pattern occurrence.
    """
    for pattern in key_patterns:
        for m in re.finditer(pattern, text):
            start = m.end()
            segment = text[start:start+35]
            # Chinese size names
            m2 = re.search(r"(小[一二三四五六]|初[一二三四]|[一二三四五六七八九十]+号)", segment)
            if m2:
                val = CHINESE_FONT_SIZE_MAP.get(m2.group(1))
                if val:
                    return val
            # Arabic numeral + 号
            m2 = re.search(r"(小)?\s*(\d+)\s*号", segment)
            if m2:
                prefix = m2.group(1) or ""
                num = int(m2.group(2))
                if prefix == "小":
                    # "小4号" → "小四" (no 号 suffix for 小-prefixed sizes)
                    cn_map_small = {1: "小一", 2: "小二", 3: "小三", 4: "小四", 5: "小五", 6: "小六"}
                    size_name = cn_map_small.get(num, "")
                else:
                    cn_map = {1: "一号", 2: "二号", 3: "三号", 4: "四号", 5: "五号", 6: "六号", 7: "七号"}
                    size_name = cn_map.get(num, "")
                if size_name:
                    val = CHINESE_FONT_SIZE_MAP.get(size_name)
                    if val:
                        return val
            # pt / 磅
            m2 = re.search(r"([\d\.]+)\s*磅", segment)
            if m2:
                return float(m2.group(1))
    return None


def _extract_chars(text: str, key_patterns: list[str]) -> float | None:
    """Extract character count for indent (2字符 = 24pt for 小四)."""
    for pattern in key_patterns:
        m = re.search(pattern + r"([\d一二两三四五六七八九十]+)\s*(?:个)?(?:汉字)?字符?", text)
        if m:
            val = _parse_cn_number(m.group(1))
            if val is not None:
                return val * 12.0
    return None


def _extract_alignment(text: str, key_patterns: list[str]) -> Alignment | None:
    """Extract alignment for a key pattern. Search within 30 chars after the key."""
    for pattern in key_patterns:
        # Find the pattern, then look for alignment keyword within 40 chars
        for m in re.finditer(pattern, text):
            start = m.end()
            # Take up to 40 chars after the pattern
            segment = text[start:start+40]
            if re.search(r"居中", segment):
                return Alignment.CENTER
            if re.search(r"左对齐|顶格|左对", segment):
                return Alignment.LEFT
            if re.search(r"右对齐", segment):
                return Alignment.RIGHT
            if re.search(r"两端对齐|两对齐", segment):
                return Alignment.JUSTIFY
    return None


def _pattern_parse(text: str) -> FormatRuleSet:
    """Parse Chinese format requirements using regex pattern matching."""
    rs = FormatRuleSet()

    # Page margins — support multiple naming conventions
    mt = _extract_cm(text, [r"上边距", r"上(?:边)?距", r"天头[^\n]*?"])
    mb = _extract_cm(text, [r"下边距", r"下(?:边)?距", r"地角[^\n]*?", r"地脚[^\n]*?"])
    ml = _extract_cm(text, [r"左边距", r"左(?:边)?距", r"订口[^\n]*?"])
    mr = _extract_cm(text, [r"右边距", r"右(?:边)?距", r"翻口[^\n]*?"])

    # Page size
    if "a4" in text.lower():
        rs.document_level.page_width = 595.3
        rs.document_level.page_height = 841.9

    if any(v is not None for v in (mt, mb, ml, mr)):
        rs.document_level.margin_top = mt
        rs.document_level.margin_bottom = mb
        rs.document_level.margin_left = ml
        rs.document_level.margin_right = mr

    # Default font
    if "宋体" in text:
        rs.document_level.default_font = FontFormat(
            font_name="Times New Roman", font_name_east_asia="宋体", font_size=12.0
        )

    # Line spacing: fixed value or multiple
    m_fixed = re.search(r"行距.*?固定.*?([\d点二两三四五六七八九十〇．\.]+)\s*磅", text)
    if m_fixed:
        val = _parse_cn_number(m_fixed.group(1))
        if val is not None:
            body_para = ParagraphFormat(line_spacing=val, line_spacing_rule="exact")
        else:
            body_para = ParagraphFormat(line_spacing=1.5)
    else:
        # Check for single line spacing first
        if re.search(r"单倍行距", text):
            body_para = ParagraphFormat(line_spacing=1.0, line_spacing_rule="multiple")
        else:
            m_mult = re.search(r"行距.*?([\d\.]+)\s*倍", text)
            if m_mult:
                body_para = ParagraphFormat(line_spacing=float(m_mult.group(1)))
            else:
                body_para = ParagraphFormat()
    if "段前段后" in text:
        after = text[text.index("段前段后"):]
        if "零" in after[:20]:
            body_para.space_before = 0.0
            body_para.space_after = 0.0

    # Body first line indent
    body_indent = _extract_chars(text, [r"正文[^\n]*首行缩进", r"首行缩进"])
    if body_indent is not None:
        body_para.first_line_indent = body_indent

    # Body font — most specific patterns first (first match wins)
    body_size = _extract_font_size(text, [
        r"正文文字一般用", r"正文内容使用", r"正文字体为",
        r"正文文字", r"正文内容", r"正文用",
    ])
    body_font = FontFormat(
        font_name="Times New Roman",
        font_name_east_asia="宋体" if "宋体" in text else None,
        font_size=body_size or 12.0,
    )
    body_align = _extract_alignment(text, [r"正文[^\n]*"])
    if body_align:
        body_para.alignment = body_align
    rs.styles["Body"] = StyleFormat(font=body_font, paragraph=body_para)

    # Title (大标题/论文标题)
    title_size = _extract_font_size(text, [r"论文标题", r"大标题", r"论文大标题", r"题目"])
    title_font_name = "黑体" if "黑体" in text else None
    title_align = _extract_alignment(text, [r"论文标题", r"大标题", r"论文大标题", r"题目"])
    # Also check standalone "居中" near title mentions
    if title_align is None and re.search(r"标题[^\n]*?居中", text):
        title_align = Alignment.CENTER
    title_font = FontFormat(
        font_name="Times New Roman" if title_font_name else None,
        font_name_east_asia=title_font_name,
        font_size=title_size,
        bold=True if title_size else None,
    )
    title_para = ParagraphFormat(alignment=title_align, space_before=0.0, space_after=0.0)
    rs.styles["Title"] = StyleFormat(font=title_font, paragraph=title_para)

    # Heading 1 (一级标题)
    h1_size = _extract_font_size(text, [r"一级标题", r"一级标题标题序号"])
    h1_font = FontFormat(
        font_name="Times New Roman",
        font_name_east_asia="黑体" if "黑体" in text else None,
        font_size=h1_size,
        bold=True if h1_size else None,
    )
    h1_para = ParagraphFormat(space_before=0.0, space_after=0.0)
    h1_align = _extract_alignment(text, [r"一级标题"])
    if h1_align:
        h1_para.alignment = h1_align
    if re.search(r"一级标题[^\n]*顶格", text):
        h1_para.first_line_indent = 0.0
    rs.styles["Heading1"] = StyleFormat(font=h1_font, paragraph=h1_para)

    # Heading 2 (二级标题)
    h2_size = _extract_font_size(text, [r"二级标题"])
    # "与正文字号相同" → use body size
    if h2_size is None and re.search(r"二级标题[^\n]*?与正文字号相同", text):
        h2_size = body_font.font_size
    h2_font = FontFormat(
        font_name="Times New Roman",
        font_name_east_asia="黑体" if "黑体" in text else None,
        font_size=h2_size,
        bold=True if h2_size else None,
    )
    h2_para = ParagraphFormat(space_before=0.0, space_after=0.0)
    h2_indent = _extract_chars(text, [r"二级标题[^\n]*?缩进"])
    if h2_indent is not None:
        h2_para.first_line_indent = h2_indent
    rs.styles["Heading2"] = StyleFormat(font=h2_font, paragraph=h2_para)

    # Heading 3 (三级标题)
    h3_size = _extract_font_size(text, [r"三级标题"])
    h3_font = FontFormat(
        font_name="Times New Roman",
        font_name_east_asia="黑体" if "黑体" in text else None,
        font_size=h3_size,
        bold=True if h3_size else None,
    )
    h3_para = ParagraphFormat(space_before=0.0, space_after=0.0)
    h3_indent = _extract_chars(text, [r"三级标题[^\n]*?缩进"])
    if h3_indent is not None:
        h3_para.first_line_indent = h3_indent
    rs.styles["Heading3"] = StyleFormat(font=h3_font, paragraph=h3_para)

    # Caption (图表标题)
    cap_size = _extract_font_size(text, [r"图表标题", r"图表名称"])
    if cap_size:
        rs.styles["Caption"] = StyleFormat(
            font=FontFormat(font_name="Times New Roman", font_name_east_asia="宋体", font_size=cap_size),
            paragraph=ParagraphFormat(alignment=Alignment.CENTER),
        )

    # Reference
    if "参考文献" in text:
        # Content size: look for "内容为" or "内容用" pattern after 参考文献 heading mention
        ref_size = None
        m = re.search(r"参考文献[^\n]*?内容为[^\n]*?(小[一二三四五六]|初[一二三四]|[一二三四五六七八九十]+号)", text)
        if m:
            ref_size = CHINESE_FONT_SIZE_MAP.get(m.group(1))
        if ref_size is None:
            m = re.search(r"参考文献[^\n]*?内容为[^\n]*?(小)?\s*(\d+)\s*号", text)
            if m:
                prefix = m.group(1) or ""
                num = int(m.group(2))
                if prefix == "小":
                    cn_map_small = {1: "小一", 2: "小二", 3: "小三", 4: "小四", 5: "小五", 6: "小六"}
                    ref_size = CHINESE_FONT_SIZE_MAP.get(cn_map_small.get(num, ""))
                else:
                    cn_map = {1: "一号", 2: "二号", 3: "三号", 4: "四号", 5: "五号", 6: "六号", 7: "七号"}
                    ref_size = CHINESE_FONT_SIZE_MAP.get(cn_map.get(num, ""))
        if "Reference" in rs.styles:
            if ref_size:
                rs.styles["Reference"].font.font_size = ref_size
            rs.styles["Reference"].paragraph.first_line_indent = None
            rs.styles["Reference"].paragraph.left_indent = 24.0
            rs.styles["Reference"].paragraph.line_spacing = 1.5
            rs.styles["Reference"].paragraph.line_spacing_rule = "multiple"
        else:
            rs.styles["Reference"] = StyleFormat(
                font=FontFormat(
                    font_name="Times New Roman",
                    font_name_east_asia="宋体",
                    font_size=ref_size or 10.5,
                ),
                paragraph=ParagraphFormat(
                    alignment=Alignment.JUSTIFY,
                    line_spacing=1.5,
                    left_indent=24.0,
                ),
            )

    return rs


def parse_requirement(text: str, preset_id: str | None = None) -> FormatRuleSet:
    """Parse a natural-language format requirement into a FormatRuleSet.

    1. Match a preset template (by explicit ID or keyword scan).
    2. Pattern-match the text (regex-based, no LLM needed).
    3. Call LLM to parse the text into structured rules (null for unspecified).
    4. Merge: academic defaults → preset → pattern-match → LLM override.
    5. Track source labels.
    """
    preset: dict | None = None
    if preset_id:
        preset = get_preset_by_id(preset_id)
    if preset is None:
        preset = match_preset(text)

    # Start from academic defaults
    result = _ACADEMIC_DEFAULTS.model_copy(deep=True)

    # Layer preset on top if available
    if preset:
        result = _merge_into(result, preset["rule_set"], "preset")

    # Pattern-match the text (always, even if LLM is available)
    pattern_parsed = _pattern_parse(text)
    result = _merge_into(result, pattern_parsed, "text_parse")

    # If LLM is available, parse the text and merge on top
    parsed: FormatRuleSet | None = pattern_parsed
    if llm_client.available:
        try:
            raw = llm_client.chat_json(_SYSTEM_PROMPT, text, temperature=0.1, max_tokens=4096)
            llm_parsed = _parse_llm_response(raw)
            result = _merge_into(result, llm_parsed, "text_parse")
            parsed = llm_parsed
        except Exception as exc:
            logger.error("LLM requirement parsing failed: %s", exc)
    else:
        logger.warning("LLM not available — using preset/pattern-match/defaults")

    preset_rs = preset["rule_set"] if preset else None
    _record_sources(result, parsed, preset_rs)

    return result
