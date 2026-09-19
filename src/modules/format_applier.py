"""Format applier — maps optimized text to FormatRuleSet styles, preparing data
for the document generator."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from src.models import (
    DocumentObject,
    FormatRuleSet,
    ParagraphOptimization,
    StyleFormat,
)
from src.modules.heading_numbering import apply_heading_numbers

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


@dataclass
class FormattedParagraph:
    text: str
    style_key: str  # key into FormatRuleSet.styles
    is_heading: bool = False
    heading_level: int = 0


@dataclass
class FormattedDocument:
    paragraphs: list[FormattedParagraph] = field(default_factory=list)
    tables: list[list[list[str]]] = field(default_factory=list)
    rule_set: FormatRuleSet | None = None


def _looks_like_title(text: str) -> bool:
    """Heuristic: short text without sentence-ending punctuation looks like a title."""
    stripped = text.strip()
    if not stripped or len(stripped) > 60:
        return False
    return not stripped.endswith(("。", "！", "？", ".", "!", "?", ";", "；"))


def _map_style_key(
    style_name: str,
    is_heading: bool,
    heading_level: int,
    text: str = "",
    is_first_nonempty: bool = False,
    has_title_style: bool = False,
) -> str:
    mapped = _STYLE_NAME_MAP.get(style_name.strip().lower(), "")
    if mapped:
        return mapped
    if is_heading:
        return f"Heading{min(heading_level, 3)}"
    if is_first_nonempty and has_title_style and _looks_like_title(text):
        return "Title"
    return "Body"


_REF_HEADINGS = {"参考文献", "参考资料", "references", "bibliography"}


def _is_ref_heading(text: str) -> bool:
    """Check if text is a references heading."""
    stripped = text.strip().lower()
    return stripped in _REF_HEADINGS


def apply_format(
    doc_obj: DocumentObject,
    optimization_result,
    rule_set: FormatRuleSet,
) -> FormattedDocument:
    """Map optimized paragraphs to FormatRuleSet styles and build a FormattedDocument.

    optimization_result can be an OptimizationResult or None (skip optimization).
    """
    opt_map: dict[int, str] = {}
    if optimization_result is not None:
        for p in optimization_result.paragraphs:
            opt_map[p.index] = p.optimized_text

    has_title_style = "Title" in rule_set.styles
    has_ref_style = "Reference" in rule_set.styles
    title_assigned = False
    in_ref_section = False

    formatted_paras: list[FormattedParagraph] = []
    for para in doc_obj.paragraphs:
        text = opt_map.get(para.index, para.text)
        stripped = text.strip()

        # Detect references section boundary
        if _is_ref_heading(stripped):
            in_ref_section = True
        elif in_ref_section and para.is_heading and stripped:
            in_ref_section = False

        is_first_nonempty = not title_assigned and stripped != ""
        if is_first_nonempty and has_title_style:
            title_assigned = True

        style_key = _map_style_key(
            para.style_name, para.is_heading, para.heading_level,
            text=text, is_first_nonempty=is_first_nonempty,
            has_title_style=has_title_style,
        )

        # References section: non-heading, non-empty paragraphs → Reference style
        if in_ref_section and has_ref_style and not para.is_heading and stripped:
            if not _is_ref_heading(stripped):
                style_key = "Reference"

        if style_key not in rule_set.styles and style_key != "Body":
            style_key = "Body"

        formatted_paras.append(
            FormattedParagraph(
                text=text,
                style_key=style_key,
                is_heading=para.is_heading,
                heading_level=para.heading_level,
            )
        )

    # Apply heading auto-numbering if enabled
    if rule_set.heading_numbering.enabled:
        formatted_paras = apply_heading_numbers(formatted_paras, rule_set.heading_numbering)

    tables = [t.cells for t in doc_obj.tables]

    return FormattedDocument(
        paragraphs=formatted_paras,
        tables=tables,
        rule_set=rule_set,
    )
