"""Format extractor — builds a FormatRuleSet from a parsed DocumentObject (Method A).

Supports two modes:
- Template mode: extract format from the document's own formatting (styles, fonts, etc.)
- Annotation mode: extract format from text box annotations (批注类要求)
- Auto mode: detect which mode applies and use it (or merge both)
"""

from __future__ import annotations

import logging
import os
from collections import Counter
from typing import Any

from src.models import (
    Alignment,
    DocumentLevel,
    DocumentObject,
    FontFormat,
    FormatRuleSet,
    HeadingNumbering,
    ParagraphFormat,
    ParagraphInfo,
    StyleFormat,
)
from src.modules.textbox_extractor import extract_text_boxes
from src.modules.textbox_parser import parse_textbox_requirements, _is_format_requirement

logger = logging.getLogger(__name__)

_STYLE_NAME_MAP = {
    "title": "Title", "标题": "Title",
    "heading 1": "Heading1", "标题 1": "Heading1",
    "heading 2": "Heading2", "标题 2": "Heading2",
    "heading 3": "Heading3", "标题 3": "Heading3",
    "heading 4": "Heading3", "标题 4": "Heading3",
    "caption": "Caption", "题注": "Caption",
    "table text": "TableText", "表格文本": "TableText",
    "reference": "Reference", "参考文献": "Reference",
    "footnote text": "Reference", "脚注文本": "Reference",
    "subtitle": "Heading1", "副标题": "Heading1",
}

# Styles we care about extracting
_TARGET_STYLES = {"Title", "Heading1", "Heading2", "Heading3", "Body", "Caption", "TableText", "Reference"}


def _map_style_name(style_name: str) -> str:
    return _STYLE_NAME_MAP.get(style_name.strip().lower(), "")


def _most_common_font(paras: list[ParagraphInfo]) -> FontFormat:
    """Pick the most frequent font attributes across a group of paragraphs."""
    names = [p.font.font_name for p in paras if p.font.font_name]
    east_names = [p.font.font_name_east_asia for p in paras if p.font.font_name_east_asia]
    sizes = [p.font.font_size for p in paras if p.font.font_size is not None]
    bolds = [p.font.bold for p in paras if p.font.bold is not None]

    def mode(values: list[Any]):
        return Counter(values).most_common(1)[0][0] if values else None

    return FontFormat(
        font_name=mode(names),
        font_name_east_asia=mode(east_names),
        font_size=mode(sizes),
        bold=mode(bolds),
    )


def _most_common_para_fmt(paras: list[ParagraphInfo]) -> ParagraphFormat:
    """Pick the most frequent paragraph format attributes across a group."""
    alignments = [p.paragraph.alignment for p in paras if p.paragraph.alignment is not None]
    line_spacings = [p.paragraph.line_spacing for p in paras if p.paragraph.line_spacing is not None]
    space_befores = [p.paragraph.space_before for p in paras if p.paragraph.space_before is not None]
    space_afters = [p.paragraph.space_after for p in paras if p.paragraph.space_after is not None]
    indents = [p.paragraph.first_line_indent for p in paras if p.paragraph.first_line_indent is not None]

    def mode(values: list[Any]):
        return Counter(values).most_common(1)[0][0] if values else None

    return ParagraphFormat(
        alignment=mode(alignments),
        line_spacing=mode(line_spacings),
        space_before=mode(space_befores),
        space_after=mode(space_afters),
        first_line_indent=mode(indents),
    )


def _build_document_level(doc_obj: DocumentObject) -> DocumentLevel:
    default_font = FontFormat()
    body_paras = [p for p in doc_obj.paragraphs if not p.is_heading and p.text.strip()]
    if body_paras:
        default_font = _most_common_font(body_paras)

    return DocumentLevel(
        page_width=doc_obj.page_width,
        page_height=doc_obj.page_height,
        margin_top=doc_obj.margin_top,
        margin_bottom=doc_obj.margin_bottom,
        margin_left=doc_obj.margin_left,
        margin_right=doc_obj.margin_right,
        header=doc_obj.header,
        footer=doc_obj.footer,
        default_font=default_font,
    )


def _build_styles(doc_obj: DocumentObject) -> dict[str, StyleFormat]:
    """Group paragraphs by mapped style name and extract the common format for each."""
    groups: dict[str, list[ParagraphInfo]] = {}
    for para in doc_obj.paragraphs:
        mapped = _map_style_name(para.style_name)
        if not mapped:
            if para.is_heading:
                mapped = f"Heading{para.heading_level}" if para.heading_level <= 3 else "Heading3"
            elif para.text.strip():
                mapped = "Body"
            else:
                continue
        groups.setdefault(mapped, []).append(para)

    styles: dict[str, StyleFormat] = {}
    for style_name, paras in groups.items():
        if style_name not in _TARGET_STYLES:
            continue
        font = _most_common_font(paras)
        para_fmt = _most_common_para_fmt(paras)
        styles[style_name] = StyleFormat(font=font, paragraph=para_fmt)

    # Fallback: if Body is missing, derive from any non-heading paragraph
    if "Body" not in styles:
        body_paras = [p for p in doc_obj.paragraphs if not p.is_heading and p.text.strip()]
        if body_paras:
            styles["Body"] = StyleFormat(
                font=_most_common_font(body_paras),
                paragraph=_most_common_para_fmt(body_paras),
            )
        else:
            # No body paragraphs at all — create a default Body style
            styles["Body"] = StyleFormat(
                font=FontFormat(font_name="Times New Roman", font_name_east_asia="宋体", font_size=12.0),
                paragraph=ParagraphFormat(alignment=Alignment.JUSTIFY, line_spacing=1.5, first_line_indent=24.0),
            )

    return styles


def extract_format_rules(doc_obj: DocumentObject, docx_path: str | None = None) -> FormatRuleSet:
    """Build a complete FormatRuleSet from a parsed DocumentObject.
    
    If docx_path is provided, also checks for text box annotations (批注类要求).
    When text boxes with format requirements are found, they take priority
    over the document's own formatting, since they represent the explicit
    specification rather than the example formatting.
    """
    doc_level = _build_document_level(doc_obj)
    styles = _build_styles(doc_obj)

    sources = {key: "template" for key in styles}
    sources["document_level"] = "template"

    # Check for text box annotations (批注类要求)
    textbox_rules = None
    if docx_path and os.path.exists(docx_path):
        text_boxes = extract_text_boxes(docx_path)
        format_boxes = [tb for tb in text_boxes if _is_format_requirement(tb.text)]
        
        if format_boxes:
            logger.info("Found %d text boxes with format requirements", len(format_boxes))
            textbox_texts = [tb.text for tb in format_boxes]
            textbox_rules = parse_textbox_requirements(textbox_texts)
            
            # Merge: text box rules take priority over template-extracted rules
            for style_key, style_fmt in textbox_rules.styles.items():
                if style_key in styles:
                    # Merge: text box overrides template for each attribute
                    existing = styles[style_key]
                    if style_fmt.font.font_name:
                        existing.font.font_name = style_fmt.font.font_name
                    if style_fmt.font.font_name_east_asia:
                        existing.font.font_name_east_asia = style_fmt.font.font_name_east_asia
                    if style_fmt.font.font_size:
                        existing.font.font_size = style_fmt.font.font_size
                    if style_fmt.font.bold is not None:
                        existing.font.bold = style_fmt.font.bold
                    if style_fmt.paragraph.alignment is not None:
                        existing.paragraph.alignment = style_fmt.paragraph.alignment
                    if style_fmt.paragraph.line_spacing is not None:
                        existing.paragraph.line_spacing = style_fmt.paragraph.line_spacing
                        existing.paragraph.line_spacing_rule = style_fmt.paragraph.line_spacing_rule
                    if style_fmt.paragraph.first_line_indent is not None:
                        existing.paragraph.first_line_indent = style_fmt.paragraph.first_line_indent
                    if style_fmt.paragraph.left_indent is not None:
                        existing.paragraph.left_indent = style_fmt.paragraph.left_indent
                    if style_fmt.paragraph.space_before is not None:
                        existing.paragraph.space_before = style_fmt.paragraph.space_before
                    if style_fmt.paragraph.space_after is not None:
                        existing.paragraph.space_after = style_fmt.paragraph.space_after
                    sources[style_key] = "textbox"
                else:
                    # New style from text box only
                    styles[style_key] = style_fmt
                    sources[style_key] = "textbox"

    return FormatRuleSet(
        document_level=doc_level,
        styles=styles,
        heading_numbering=HeadingNumbering(),
        sources=sources,
    )
