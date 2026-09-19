"""Document generator — writes a FormattedDocument to a .docx file using python-docx."""

from __future__ import annotations

import logging

from docx import Document
from docx.shared import Pt, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from src.models import Alignment, FontFormat, FormatRuleSet, ParagraphFormat, StyleFormat
from src.modules.format_applier import FormattedDocument
from src.modules.toc_generator import insert_toc
from src.modules.section_manager import _set_page_number_format, _add_page_number_field

logger = logging.getLogger(__name__)

_ALIGN_MAP = {
    Alignment.LEFT: WD_ALIGN_PARAGRAPH.LEFT,
    Alignment.CENTER: WD_ALIGN_PARAGRAPH.CENTER,
    Alignment.RIGHT: WD_ALIGN_PARAGRAPH.RIGHT,
    Alignment.JUSTIFY: WD_ALIGN_PARAGRAPH.JUSTIFY,
}


def _apply_font_to_run(run, font_fmt, style: StyleFormat):
    """Apply font format to a run, including East Asian font via XML."""
    font = style.font
    name = font.font_name or font_fmt.font_name
    east = font.font_name_east_asia or font_fmt.font_name_east_asia
    size = font.font_size if font.font_size is not None else font_fmt.font_size
    bold = font.bold if font.bold is not None else font_fmt.bold

    if name:
        run.font.name = name
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold

    # Set East Asian font via XML
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = rPr.makeelement(qn("w:rFonts"), {})
        rPr.insert(0, rFonts)
    if east:
        rFonts.set(qn("w:eastAsia"), east)
    if name:
        rFonts.set(qn("w:ascii"), name)
        rFonts.set(qn("w:hAnsi"), name)


def _apply_paragraph_format(para, style: StyleFormat):
    """Apply paragraph-level format from a StyleFormat."""
    pf = style.paragraph
    if pf.alignment:
        para.alignment = _ALIGN_MAP.get(pf.alignment, WD_ALIGN_PARAGRAPH.LEFT)
    if pf.line_spacing is not None:
        if pf.line_spacing_rule == "exact" or (pf.line_spacing > 3 and pf.line_spacing_rule != "multiple"):
            para.paragraph_format.line_spacing = Pt(pf.line_spacing)
            para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        else:
            para.paragraph_format.line_spacing = pf.line_spacing
    if pf.space_before is not None:
        para.paragraph_format.space_before = Pt(pf.space_before)
    if pf.space_after is not None:
        para.paragraph_format.space_after = Pt(pf.space_after)
    if pf.first_line_indent is not None:
        para.paragraph_format.first_line_indent = Pt(pf.first_line_indent)
    if pf.left_indent is not None:
        para.paragraph_format.left_indent = Pt(pf.left_indent)
    if pf.right_indent is not None:
        para.paragraph_format.right_indent = Pt(pf.right_indent)


def _set_page_setup(doc: Document, rule_set: FormatRuleSet):
    """Configure page size, margins, header, and footer from the rule set."""
    dl = rule_set.document_level
    if not doc.sections:
        return
    section = doc.sections[0]

    if dl.page_width:
        section.page_width = Emu(int(dl.page_width * 12700))
    if dl.page_height:
        section.page_height = Emu(int(dl.page_height * 12700))
    if dl.margin_top is not None:
        section.top_margin = Pt(dl.margin_top)
    if dl.margin_bottom is not None:
        section.bottom_margin = Pt(dl.margin_bottom)
    if dl.margin_left is not None:
        section.left_margin = Pt(dl.margin_left)
    if dl.margin_right is not None:
        section.right_margin = Pt(dl.margin_right)

    if dl.header:
        for para in section.header.paragraphs:
            para.text = ""
        hdr_para = section.header.paragraphs[0] if section.header.paragraphs else section.header.add_paragraph()
        hdr_para.text = dl.header
        hdr_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if dl.default_font.font_name:
            for run in hdr_para.runs:
                run.font.name = dl.default_font.font_name
                run.font.size = Pt(dl.default_font.font_size or 10.5)
                rPr = run._element.get_or_add_rPr()
                rFonts = rPr.find(qn("w:rFonts"))
                if rFonts is None:
                    rFonts = rPr.makeelement(qn("w:rFonts"), {})
                    rPr.insert(0, rFonts)
                if dl.default_font.font_name_east_asia:
                    rFonts.set(qn("w:eastAsia"), dl.default_font.font_name_east_asia)

    if dl.footer:
        for para in section.footer.paragraphs:
            para.text = ""
        ftr_para = section.footer.paragraphs[0] if section.footer.paragraphs else section.footer.add_paragraph()
        ftr_para.text = dl.footer
        ftr_para.alignment = WD_ALIGN_PARAGRAPH.CENTER


def _find_first_heading_index(formatted: FormattedDocument) -> int:
    """Find the index of the first Heading1 paragraph (main content start)."""
    for i, para in enumerate(formatted.paragraphs):
        if para.style_key == "Heading1":
            return i
    return 0


def _configure_footer_pagenumber(section, font_fmt, fmt="decimal", start=1) -> None:
    """Configure a section's footer with page number."""
    from src.models import PageNumberingFormat

    format_map = {
        "decimal": PageNumberingFormat.DECIMAL,
        "roman_upper": PageNumberingFormat.ROMAN_UPPER,
        "roman_lower": PageNumberingFormat.ROMAN_LOWER,
        "chinese": PageNumberingFormat.CHINESE,
    }
    pg_fmt = format_map.get(fmt, PageNumberingFormat.DECIMAL)
    _set_page_number_format(section, pg_fmt, start)

    # Add page number to footer center
    footer = section.footer
    for para in footer.paragraphs:
        para.clear()
    para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    _add_page_number_field(para, "center")
    # Apply font
    for run in para.runs:
        if font_fmt.font_size:
            run.font.size = Pt(font_fmt.font_size or 10.5)
        if font_fmt.font_name:
            run.font.name = font_fmt.font_name
        rPr = run._element.get_or_add_rPr()
        rFonts = rPr.find(qn("w:rFonts"))
        if rFonts is None:
            rFonts = rPr.makeelement(qn("w:rFonts"), {})
            rPr.insert(0, rFonts)
        if font_fmt.font_name_east_asia:
            rFonts.set(qn("w:eastAsia"), font_fmt.font_name_east_asia)
        if font_fmt.font_name:
            rFonts.set(qn("w:ascii"), font_fmt.font_name)
            rFonts.set(qn("w:hAnsi"), font_fmt.font_name)


def generate_document(formatted: FormattedDocument, output_path: str) -> str:
    """Write a FormattedDocument to a .docx file. Returns the output path."""
    rule_set = formatted.rule_set
    if rule_set is None:
        raise ValueError("FormattedDocument has no FormatRuleSet")

    doc = Document()
    _set_page_setup(doc, rule_set)

    body_style = rule_set.styles.get("Body", StyleFormat(
        font=FontFormat(font_name="Times New Roman", font_name_east_asia="宋体", font_size=12.0),
        paragraph=ParagraphFormat(alignment=Alignment.JUSTIFY, line_spacing=1.5, first_line_indent=24.0),
    ))
    default_font = rule_set.document_level.default_font

    # Track paragraph elements for section break insertion
    para_elements = []

    for fpara in formatted.paragraphs:
        para = doc.add_paragraph()
        para_elements.append(para._element)
        style = rule_set.styles.get(fpara.style_key, body_style)

        if fpara.text:
            run = para.add_run(fpara.text)
            _apply_font_to_run(run, default_font, style)

        _apply_paragraph_format(para, style)

    table_style = rule_set.styles.get("TableText", body_style)
    for table_cells in formatted.tables:
        if not table_cells:
            continue
        rows = len(table_cells)
        cols = max(len(r) for r in table_cells) if table_cells else 0
        if cols == 0:
            continue
        table = doc.add_table(rows=rows, cols=cols)
        try:
            table.style = "Table Grid"
        except Exception:
            pass
        for r_idx, row in enumerate(table_cells):
            for c_idx, cell_text in enumerate(row):
                if c_idx < cols:
                    try:
                        cell = table.rows[r_idx].cells[c_idx]
                    except Exception:
                        continue
                    cell.text = ""
                    if cell_text:
                        run = cell.paragraphs[0].add_run(cell_text)
                        _apply_font_to_run(run, default_font, table_style)

    # --- TOC insertion ---
    toc_opts = rule_set.toc
    if toc_opts.enabled:
        # Insert TOC at the beginning of the document
        insert_toc(doc, toc_opts, rule_set, position=0)

    # --- Section management and page numbering ---
    sec_opts = rule_set.sections
    if sec_opts.enabled and sec_opts.sections:
        sections = sec_opts.sections
        # Find where to split sections
        first_h1_idx = _find_first_heading_index(formatted)

        if len(sections) >= 2 and first_h1_idx > 0:
            # Two-section layout:
            #   Section 1: front matter (title, abstract, TOC) - Roman numerals
            #   Section 2: main body + references - Arabic numerals starting from 1
            front_section_cfg = sections[0]
            main_section_cfg = sections[1] if len(sections) > 1 else sections[0]

            # Add a section break before the first Heading1
            # We need to find the paragraph element and insert a sectPr before it
            if first_h1_idx < len(para_elements):
                target_elem = para_elements[first_h1_idx]

                # Create a new section by adding section break paragraph
                # python-docx adds sections at the end, so we need to manipulate XML
                # Approach: add a new section, then move its sectPr to the right place
                new_section = doc.add_section(WD_SECTION.NEW_PAGE)

                # Copy page setup from first section
                first_sec = doc.sections[0]
                new_section.page_width = first_sec.page_width
                new_section.page_height = first_sec.page_height
                new_section.top_margin = first_sec.top_margin
                new_section.bottom_margin = first_sec.bottom_margin
                new_section.left_margin = first_sec.left_margin
                new_section.right_margin = first_sec.right_margin

                # Configure front section (section 0) page numbering
                if front_section_cfg.page_numbering_enabled:
                    _configure_footer_pagenumber(
                        doc.sections[0],
                        default_font,
                        fmt=front_section_cfg.page_numbering_format.value,
                        start=front_section_cfg.page_numbering_start,
                    )
                    if front_section_cfg.header_text:
                        _set_header_text(doc.sections[0], front_section_cfg.header_text, default_font)

                # Configure main section (section 1) page numbering
                if main_section_cfg.page_numbering_enabled:
                    _configure_footer_pagenumber(
                        doc.sections[1],
                        default_font,
                        fmt=main_section_cfg.page_numbering_format.value,
                        start=main_section_cfg.page_numbering_start,
                    )
                    if main_section_cfg.header_text:
                        _set_header_text(doc.sections[1], main_section_cfg.header_text, default_font)
        else:
            # Single section with page numbering
            cfg = sections[0]
            if cfg.page_numbering_enabled:
                _configure_footer_pagenumber(
                    doc.sections[0],
                    default_font,
                    fmt=cfg.page_numbering_format.value,
                    start=cfg.page_numbering_start,
                )

    doc.save(output_path)
    logger.info("Generated document: %s", output_path)
    return output_path


def _set_header_text(section, text: str, font_fmt) -> None:
    """Set header text for a section."""
    header = section.header
    for para in header.paragraphs:
        para.clear()
    para = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    para.text = text
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in para.runs:
        if font_fmt.font_size:
            run.font.size = Pt(font_fmt.font_size or 10.5)
        if font_fmt.font_name:
            run.font.name = font_fmt.font_name
        rPr = run._element.get_or_add_rPr()
        rFonts = rPr.find(qn("w:rFonts"))
        if rFonts is None:
            rFonts = rPr.makeelement(qn("w:rFonts"), {})
            rPr.insert(0, rFonts)
        if font_fmt.font_name_east_asia:
            rFonts.set(qn("w:eastAsia"), font_fmt.font_name_east_asia)
        if font_fmt.font_name:
            rFonts.set(qn("w:ascii"), font_fmt.font_name)
            rFonts.set(qn("w:hAnsi"), font_fmt.font_name)
