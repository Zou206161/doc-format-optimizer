"""Table of Contents (TOC) generator for python-docx.

Inserts a Word TOC field that auto-updates when the document is opened in Word.
Also supports manual TOC generation with placeholder page numbers.
"""

from __future__ import annotations

import logging

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from src.models import FormatRuleSet, StyleFormat, TOCOptions
from src.modules.format_applier import FormattedParagraph, FormattedDocument

logger = logging.getLogger(__name__)


def _add_toc_field(paragraph, depth: int = 3) -> None:
    """Insert a Word TOC field into a paragraph.

    The TOC field will be automatically updated by Word when the document is opened.
    Field code: TOC \\o "1-3" \\h \\z \\u
      - \\o "1-3": outline levels 1-3
      - \\h: hyperlinks
      - \\z: hide page numbers in web view
      - \\u: use outline levels
    """
    run = paragraph.add_run()
    fldChar_begin = OxmlElement("w:fldChar")
    fldChar_begin.set(qn("w:fldCharType"), "begin")
    run._element.append(fldChar_begin)

    run2 = paragraph.add_run()
    instrText = OxmlElement("w:instrText")
    instrText.set(qn("xml:space"), "preserve")
    instrText.text = f' TOC \\o "1-{depth}" \\h \\z \\u '
    run2._element.append(instrText)

    run3 = paragraph.add_run()
    fldChar_sep = OxmlElement("w:fldChar")
    fldChar_sep.set(qn("w:fldCharType"), "separate")
    run3._element.append(fldChar_sep)

    run4 = paragraph.add_run("请右键点击此处选择「更新域」以生成目录")
    run4.font.size = Pt(10)
    run4.font.italic = True

    run5 = paragraph.add_run()
    fldChar_end = OxmlElement("w:fldChar")
    fldChar_end.set(qn("w:fldCharType"), "end")
    run5._element.append(fldChar_end)


def _add_toc_entry_manual(
    paragraph,
    text: str,
    level: int,
    page_num: str = "",
    leader: str = "dots",
    style: StyleFormat | None = None,
) -> None:
    """Add a manual TOC entry line with leader dots and page number."""
    # Indent based on level
    indent_pt = (level - 1) * 18
    if indent_pt > 0:
        paragraph.paragraph_format.left_indent = Pt(indent_pt)

    # Add the heading text
    run = paragraph.add_run(text)
    if style:
        from src.modules.doc_generator import _apply_font_to_run
        # We can't easily call it without font_fmt, so apply basic formatting
        f = style.font
        if f.font_size:
            run.font.size = Pt(f.font_size)
        if f.bold is not None:
            run.font.bold = f.bold

    # Add tab stop for page number with leader
    tab_stops = paragraph.paragraph_format.tab_stops
    # Right-aligned tab at the right margin
    tab_stops.add_tab_stop(
        Pt(400),  # approximate, will be adjusted by page width
        WD_TAB_ALIGNMENT.RIGHT,
        WD_TAB_LEADER.DOTS if leader == "dots" else (
            WD_TAB_LEADER.HYPHENS if leader == "solid" else WD_TAB_LEADER.SPACES
        ),
    )

    # Tab character + page number placeholder
    tab_run = paragraph.add_run("\t" + page_num)
    if style:
        f = style.font
        if f.font_size:
            tab_run.font.size = Pt(f.font_size)


def insert_toc(
    doc: Document,
    toc_options: TOCOptions,
    rule_set: FormatRuleSet,
    position: int = 0,
) -> None:
    """Insert a Table of Contents into the document at the given position.

    Uses Word's TOC field for automatic page number calculation.

    Args:
        doc: python-docx Document object
        toc_options: TOC configuration
        rule_set: FormatRuleSet for styles
        position: paragraph index to insert before (0 = beginning)
    """
    if not toc_options.enabled:
        return

    # Get style for TOC title
    title_style = rule_set.styles.get(toc_options.title_style, rule_set.styles.get("Heading1"))
    toc1_style = rule_set.styles.get("Heading2", rule_set.styles.get("Body"))
    toc2_style = rule_set.styles.get("Heading3", toc1_style)

    # If new_page, add a page break before TOC title
    if toc_options.new_page and position == 0:
        # Add at beginning - we'll handle page break in the title
        pass

    # We need to insert paragraphs at the beginning.
    # python-docx doesn't have insert_paragraph_before directly,
    # so we work with the XML body.
    body = doc.element.body

    # Find the position to insert
    paras = doc.paragraphs
    if position >= len(paras):
        position = len(paras) - 1 if paras else 0

    # Insert TOC title paragraph
    title_para = doc.add_paragraph()
    title_para.text = toc_options.title
    if title_style:
        from src.modules.doc_generator import _apply_paragraph_format
        _apply_paragraph_format(title_para, title_style)
        if title_style.font.font_size:
            for run in title_para.runs:
                run.font.size = Pt(title_style.font.font_size)
                run.font.bold = title_style.font.bold

    # Insert TOC field paragraph
    toc_para = doc.add_paragraph()
    _add_toc_field(toc_para, depth=toc_options.depth)

    # Move the new paragraphs to the correct position
    # (python-docx always appends, so we need to reorder via XML)
    if position < len(paras):
        target_para = paras[position]._element
        # Move title_para
        title_para._element.getparent().remove(title_para._element)
        target_para.addprevious(title_para._element)
        # Move toc_para
        toc_para._element.getparent().remove(toc_para._element)
        title_para._element.addnext(toc_para._element)

    # Add page break after TOC if new_page
    if toc_options.new_page:
        last_para = toc_para
        last_para.paragraph_format.page_break_after = True


def build_toc_from_headings(
    formatted: FormattedDocument,
    toc_options: TOCOptions,
) -> list[FormattedParagraph]:
    """Build TOC entries from headings in the document.

    Returns a list of FormattedParagraph for the TOC.
    """
    toc_paras: list[FormattedParagraph] = []

    # TOC title
    toc_paras.append(FormattedParagraph(
        text=toc_options.title,
        style_key=toc_options.title_style,
        is_heading=True,
        heading_level=1,
    ))

    # Collect headings
    depth = toc_options.depth
    for para in formatted.paragraphs:
        if para.is_heading and para.heading_level and para.heading_level <= depth:
            # Skip the references heading if it would create a TOC entry of itself
            if para.text.strip() in ("参考文献", "目录"):
                continue
            # Use TOC style based on level
            toc_style = f"TOC{para.heading_level}" if para.heading_level > 1 else "TOC1"
            toc_paras.append(FormattedParagraph(
                text=para.text,
                style_key="Body",  # TOC entries use body-like style
                is_heading=False,
                heading_level=0,
            ))

    return toc_paras
