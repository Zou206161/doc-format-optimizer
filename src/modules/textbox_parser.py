"""Text box requirement parser — converts text box annotations into a FormatRuleSet.

Text boxes in template documents contain natural language format requirements
like "一级标题三号黑体居中加粗" or "正文: 中文为五号宋体，首行缩进二个字符，单倍行距".

This module maps each text box to the appropriate style key and extracts
font, size, alignment, indentation, spacing, and line spacing from the text.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from src.models import (
    Alignment,
    FormatRuleSet,
    StyleFormat,
    FontFormat,
    ParagraphFormat,
    DocumentLevel,
)
from src.utils.font_size_map import CHINESE_FONT_SIZE_MAP, PT_PER_CM

logger = logging.getLogger(__name__)


# --- Text box → style key mapping ---

# Keywords that indicate which style a text box describes
_STYLE_KEYWORDS: dict[str, list[str]] = {
    "Title": ["论文题目", "中文题目", "大标题", "论文标题", "论文大标题"],
    "Subtitle": ["副标题"],
    "Heading1": ["一级标题", "1级标题"],
    "Heading2": ["二级标题", "2级标题", "二级标题序数"],
    "Heading3": ["三级标题", "3级标题", "第三级"],
    "Heading4": ["四级标题", "4级标题", "第四级"],
    "Body": ["正文", "正文内容"],
    "Abstract": ["摘要正文", "摘要内容", "中文摘要"],
    "AbstractTitle": ["摘要标题", "三号黑体居中，上下各空一行"],
    "Keywords": ["关键词", "关键字"],
    "Caption": ["表题", "图题", "图序", "表序", "图表标题"],
    "Reference": ["参考文献"],
    "TOC": ["目录"],
    "Acknowledgement": ["致谢"],
    "Appendix": ["附录"],
    "PageHeader": ["页眉", "页脚"],
}

# Format keywords for parsing
_FONT_NAMES_EAST = ["宋体", "黑体", "楷体", "仿宋", "华文楷体", "华文宋体", "华文黑体"]
_FONT_NAMES_WEST = ["Times New Roman", "Arial", "Cambria", "Calibri"]
_ALIGNMENTS = {
    "居中": Alignment.CENTER,
    "左对齐": Alignment.LEFT,
    "右对齐": Alignment.RIGHT,
    "两端对齐": Alignment.JUSTIFY,
    "顶格": Alignment.LEFT,
    "顶格书写": Alignment.LEFT,
}


def _classify_textbox(text: str) -> str | None:
    """Determine which style key a text box describes.
    
    Returns None if the text box doesn't describe a format requirement.
    """
    for style_key, keywords in _STYLE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return style_key
    return None


def _extract_size(text: str) -> float | None:
    """Extract font size from text box content."""
    # Chinese size names
    m = re.search(r"(小[一二三四五六]|初[一二三四]|[一二三四五六七八九十]+号)", text)
    if m:
        return CHINESE_FONT_SIZE_MAP.get(m.group(1))
    # Arabic + 号
    m = re.search(r"(小)?\s*(\d+)\s*号", text)
    if m:
        prefix = m.group(1) or ""
        num = int(m.group(2))
        if prefix == "小":
            cn_map = {1: "小一", 2: "小二", 3: "小三", 4: "小四", 5: "小五", 6: "小六"}
            return CHINESE_FONT_SIZE_MAP.get(cn_map.get(num, ""))
        cn_map = {1: "一号", 2: "二号", 3: "三号", 4: "四号", 5: "五号", 6: "六号", 7: "七号"}
        return CHINESE_FONT_SIZE_MAP.get(cn_map.get(num, ""))
    # pt / 磅
    m = re.search(r"([\d\.]+)\s*(?:磅|pt)", text)
    if m:
        return float(m.group(1))
    return None


def _extract_font_names(text: str) -> tuple[str | None, str | None]:
    """Extract east-asian and western font names from text."""
    east = None
    west = None
    for fn in _FONT_NAMES_EAST:
        if fn in text:
            east = fn
            break
    for fn in _FONT_NAMES_WEST:
        if fn in text:
            west = fn
            break
    return east, west


def _extract_alignment(text: str) -> Alignment | None:
    """Extract alignment from text."""
    for kw, align in _ALIGNMENTS.items():
        if kw in text:
            return align
    return None


def _extract_line_spacing(text: str) -> tuple[float | None, str | None]:
    """Extract line spacing. Returns (value, rule)."""
    if "单倍行距" in text:
        return 1.0, "multiple"
    if "1.5倍" in text or "1.5 倍" in text:
        return 1.5, "multiple"
    if "两倍" in text or "2倍" in text:
        return 2.0, "multiple"
    m = re.search(r"([\d\.]+)\s*倍行距", text)
    if m:
        return float(m.group(1)), "multiple"
    m = re.search(r"固定.*?([\d\.]+)\s*磅", text)
    if m:
        return float(m.group(1)), "exact"
    return None, None


def _extract_indent(text: str) -> float | None:
    """Extract first-line indent in pt."""
    # "首行缩进二个字符" or "首行缩进2字符" or "缩进2字符"
    m = re.search(r"(?:首行)?缩进[^\d]*?([二两三四五六2-6])\s*个?\s*字符", text)
    if m:
        val = m.group(1)
        if val in ("二", "两"):
            return 24.0
        elif val == "三":
            return 36.0
        elif val == "四":
            return 48.0
        else:
            num = int(val)
            return float(num * 12.0)
    # "缩进值2字符"
    m = re.search(r"缩进值[^\d]*?(\d+)\s*字符", text)
    if m:
        return float(int(m.group(1)) * 12.0)
    # pt/磅
    m = re.search(r"缩进[^\d]*?([\d\.]+)\s*(?:磅|pt)", text)
    if m:
        return float(m.group(1))
    return None


def _extract_left_indent(text: str) -> float | None:
    """Extract left indent in pt."""
    m = re.search(r"左缩进[^\d]*?(\d+)\s*字符", text)
    if m:
        return float(int(m.group(1)) * 12.0)
    m = re.search(r"左缩进[^\d]*?([\d\.]+)\s*(?:磅|pt)", text)
    if m:
        return float(m.group(1))
    return None


def _extract_spacing(text: str) -> tuple[float | None, float | None]:
    """Extract space_before and space_after from text.
    
    Handles patterns like "上下各空一行" or "段前段后0" etc.
    """
    before = None
    after = None
    
    # "上下各空一行" → approximate one blank line ≈ font_size * 1.0
    if "上下各空一行" in text or "上下各空一" in text:
        before = 12.0  # approximate
        after = 12.0
    elif "上下各空" in text:
        m = re.search(r"上下各空(\d)行", text)
        if m:
            lines = int(m.group(1))
            before = float(lines * 12.0)
            after = float(lines * 12.0)
    
    # "段前段后均为0" or "段前0段后0"
    m = re.search(r"段前[^\d]*?([\d\.]+)", text)
    if m:
        before = float(m.group(1))
    m = re.search(r"段后[^\d]*?([\d\.]+)", text)
    if m:
        after = float(m.group(1))
    
    # "段前段后间距均调整为零" or "段前段后0"
    if "段前段后" in text and ("零" in text or "0" in text):
        before = 0.0
        after = 0.0
    
    return before, after


def _is_format_requirement(text: str) -> bool:
    """Check if a text box contains a format requirement (not just a label)."""
    format_keywords = ["号", "磅", "字体", "宋体", "黑体", "楷体", "仿宋",
                        "行距", "缩进", "对齐", "居中", "加粗", "Times",
                        "顶格", "单倍", "倍行距"]
    return any(kw in text for kw in format_keywords)


def parse_textbox_requirements(text_boxes: list[str]) -> FormatRuleSet:
    """Parse text box content into a FormatRuleSet.
    
    Each text box should describe the format of one element (title, heading, body, etc.)
    """
    styles: dict[str, StyleFormat] = {}
    doc_level = DocumentLevel(
        page_width=595.3,
        page_height=841.9,
    )
    
    for text in text_boxes:
        text = text.strip()
        if not text or not _is_format_requirement(text):
            continue
        
        style_key = _classify_textbox(text)
        if style_key is None:
            # Skip text boxes that don't map to a known style
            continue
        
        # Extract format attributes
        east_font, west_font = _extract_font_names(text)
        size = _extract_size(text)
        alignment = _extract_alignment(text)
        line_spacing, line_rule = _extract_line_spacing(text)
        first_indent = _extract_indent(text)
        left_indent = _extract_left_indent(text)
        space_before, space_after = _extract_spacing(text)
        
        # Check for bold
        bold = True if "加粗" in text or "加黑" in text else None
        
        font = FontFormat(
            font_name=west_font,
            font_name_east_asia=east_font,
            font_size=size,
            bold=bold,
        )
        
        para = ParagraphFormat(
            alignment=alignment,
            line_spacing=line_spacing,
            line_spacing_rule=line_rule,
            first_line_indent=first_indent,
            left_indent=left_indent,
            space_before=space_before,
            space_after=space_after,
        )
        
        # Merge with existing style (later text boxes can override)
        if style_key in styles:
            existing = styles[style_key]
            if not existing.font.font_name and font.font_name:
                existing.font.font_name = font.font_name
            if not existing.font.font_name_east_asia and font.font_name_east_asia:
                existing.font.font_name_east_asia = font.font_name_east_asia
            if not existing.font.font_size and font.font_size:
                existing.font.font_size = font.font_size
            if not existing.font.bold and font.bold:
                existing.font.bold = font.bold
            if not existing.paragraph.alignment and para.alignment:
                existing.paragraph.alignment = para.alignment
            if not existing.paragraph.line_spacing and para.line_spacing:
                existing.paragraph.line_spacing = para.line_spacing
                existing.paragraph.line_spacing_rule = para.line_spacing_rule
            if not existing.paragraph.first_line_indent and para.first_line_indent:
                existing.paragraph.first_line_indent = para.first_line_indent
            if not existing.paragraph.left_indent and para.left_indent:
                existing.paragraph.left_indent = para.left_indent
            if not existing.paragraph.space_before and para.space_before is not None:
                existing.paragraph.space_before = para.space_before
            if not existing.paragraph.space_after and para.space_after is not None:
                existing.paragraph.space_after = para.space_after
        else:
            styles[style_key] = StyleFormat(font=font, paragraph=para)
    
    return FormatRuleSet(
        document_level=doc_level,
        styles=styles,
    )
