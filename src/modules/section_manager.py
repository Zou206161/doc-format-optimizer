"""Section management — page numbering, headers, and footers per section.

Handles multi-section documents:
  - Cover page section (no page number, different header)
  - TOC section (Roman numerals)
  - Main content section (Arabic numerals starting from 1)
"""

from __future__ import annotations

import logging

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from src.models import (
    DocumentSections,
    FormatRuleSet,
    PageNumberingFormat,
    SectionConfig,
)

logger = logging.getLogger(__name__)


def _set_page_number_format(section, fmt: PageNumberingFormat, start: int = 1) -> None:
    """Set page numbering format and starting number for a section.

    Manipulates the section properties XML to set:
      - w:pgNumType with w:fmt and w:start
    """
    fmt_map = {
        PageNumberingFormat.DECIMAL: "decimal",
        PageNumberingFormat.ROMAN_UPPER: "upperRoman",
        PageNumberingFormat.ROMAN_LOWER: "lowerRoman",
        PageNumberingFormat.CHINESE: "chineseCounting",
    }
    w_fmt = fmt_map.get(fmt, "decimal")

    # Get or create sectPr
    sectPr = section._sectPr

    # Remove existing pgNumType
    existing = sectPr.find(qn("w:pgNumType"))
    if existing is not None:
        sectPr.remove(existing)

    # Create new pgNumType
    pgNumType = OxmlElement("w:pgNumType")
    pgNumType.set(qn("w:fmt"), w_fmt)
    pgNumType.set(qn("w:start"), str(start))
    sectPr.append(pgNumType)


def _add_page_number_field(paragraph, position: str = "center") -> None:
    """Add a PAGE field to a paragraph (for header/footer).

    position: "left", "center", "right"
    """
    align_map = {
        "left": WD_ALIGN_PARAGRAPH.LEFT,
        "center": WD_ALIGN_PARAGRAPH.CENTER,
        "right": WD_ALIGN_PARAGRAPH.RIGHT,
    }
    paragraph.alignment = align_map.get(position, WD_ALIGN_PARAGRAPH.CENTER)

    # Clear existing content
    for run in list(paragraph.runs):
        run.clear()

    run = paragraph.add_run()
    fldChar_begin = OxmlElement("w:fldChar")
    fldChar_begin.set(qn("w:fldCharType"), "begin")
    run._element.append(fldChar_begin)

    run2 = paragraph.add_run()
    instrText = OxmlElement("w:instrText")
    instrText.set(qn("xml:space"), "preserve")
    instrText.text = " PAGE "
    run2._element.append(instrText)

    run3 = paragraph.add_run()
    fldChar_end = OxmlElement("w:fldChar")
    fldChar_end.set(qn("w:fldCharType"), "end")
    run3._element.append(fldChar_end)


def _set_section_header(section, text: str | None, style_font=None) -> None:
    """Set the header text for a section."""
    header = section.header
    # Clear existing paragraphs
    for para in header.paragraphs:
        para.clear()

    if text:
        para = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
        para.text = text
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if style_font:
            for run in para.runs:
                if style_font.font_name:
                    run.font.name = style_font.font_name
                if style_font.font_size:
                    run.font.size = Pt(style_font.font_size)
                # Set East Asian font
                rPr = run._element.get_or_add_rPr()
                rFonts = rPr.find(qn("w:rFonts"))
                if rFonts is None:
                    rFonts = rPr.makeelement(qn("w:rFonts"), {})
                    rPr.insert(0, rFonts)
                if style_font.font_name_east_asia:
                    rFonts.set(qn("w:eastAsia"), style_font.font_name_east_asia)
                if style_font.font_name:
                    rFonts.set(qn("w:ascii"), style_font.font_name)
                    rFonts.set(qn("w:hAnsi"), style_font.font_name)


def _set_section_footer(
    section,
    text: str | None = None,
    show_page_number: bool = True,
    page_pos: str = "center",
    style_font=None,
) -> None:
    """Set the footer for a section (text and/or page number)."""
    footer = section.footer
    # Clear existing
    for para in footer.paragraphs:
        para.clear()

    para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()

    if show_page_number:
        _add_page_number_field(para, page_pos)

    if text:
        run = para.add_run(text)
        if style_font:
            if style_font.font_name:
                run.font.name = style_font.font_name
            if style_font.font_size:
                run.font.size = Pt(style_font.font_size)


def _add_section_break(doc: Document) -> None:
    """Add a section break (new page) to the document.

    Returns the new section.
    """
    # Add a paragraph with a section break
    para = doc.add_paragraph()
    # Use the python-docx section mechanism
    from docx.enum.section import WD_SECTION
    section = doc.add_section(WD_SECTION.NEW_PAGE)
    return section


def configure_sections(
    doc: Document,
    sections_config: DocumentSections,
    rule_set: FormatRuleSet,
) -> None:
    """Configure document sections with page numbering and headers/footers.

    Creates multiple sections with different page numbering schemes:
      - Section 0: Cover page (no page number, optional header)
      - Section 1: TOC / front matter (Roman numerals)
      - Section 2: Main content (Arabic numerals, starts from 1)

    Note: Section breaks are inserted at the end of the document.
    The calling code is responsible for placing content in the right sections.
    """
    if not sections_config.enabled or not sections_config.sections:
        return

    default_font = rule_set.document_level.default_font
    sections = sections_config.sections

    # Configure the first (default) section
    if sections:
        first = sections[0]
        _configure_single_section(doc.sections[0], first, default_font)

    # For additional sections, we need section breaks.
    # Since we don't know where exactly to break yet,
    # we set up the configuration and the document generator
    # will insert breaks at the right places.
    logger.info("Section configuration ready: %d sections", len(sections))


def _configure_single_section(section, config: SectionConfig, default_font) -> None:
    """Configure a single section's page numbering and header/footer."""
    # Page numbering
    if config.page_numbering_enabled:
        _set_page_number_format(
            section, config.page_numbering_format, config.page_numbering_start
        )

    # Header
    if config.header_text is not None:
        _set_section_header(section, config.header_text, default_font)

    # Footer with page number
    if config.footer_text is not None or config.page_numbering_enabled:
        _set_section_footer(
            section,
            text=config.footer_text,
            show_page_number=config.page_numbering_enabled,
            style_font=default_font,
        )

    # Different first page
    if config.different_first_page:
        section.different_first_page_header_footer = True


def detect_section_boundaries(formatted_doc) -> dict:
    """Detect section boundaries from document structure.

    Returns a dict with:
      - has_cover: bool (first non-empty paragraph is Title)
      - has_toc_heading: bool (there's a "目录" heading)
      - first_heading_index: int (index of first Heading1)
      - ref_heading_index: int (index of "参考文献" heading)
    """
    paras = formatted_doc.paragraphs
    result = {
        "has_cover": False,
        "has_toc_heading": False,
        "first_heading_index": -1,
        "ref_heading_index": -1,
    }

    found_first_heading = False
    for i, para in enumerate(paras):
        stripped = para.text.strip()
        if not stripped:
            continue

        # Check for title (cover page)
        if para.style_key == "Title" and not found_first_heading:
            result["has_cover"] = True

        # Check for first Heading1
        if para.style_key == "Heading1" and not found_first_heading:
            result["first_heading_index"] = i
            found_first_heading = True

        # Check for TOC heading
        if stripped == "目录":
            result["has_toc_heading"] = True

        # Check for references heading
        if stripped == "参考文献":
            result["ref_heading_index"] = i

    return result
