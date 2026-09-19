"""Pydantic data models shared across all modules."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Alignment(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


class FontFormat(BaseModel):
    font_name: str | None = None
    font_name_east_asia: str | None = None
    font_size: float | None = None
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    color: str | None = None


class ParagraphFormat(BaseModel):
    alignment: Alignment | None = None
    line_spacing: float | None = None
    line_spacing_rule: str | None = None
    space_before: float | None = None
    space_after: float | None = None
    first_line_indent: float | None = None
    left_indent: float | None = None
    right_indent: float | None = None


class StyleFormat(BaseModel):
    """A named style's full format specification."""
    font: FontFormat = Field(default_factory=FontFormat)
    paragraph: ParagraphFormat = Field(default_factory=ParagraphFormat)


class DocumentLevel(BaseModel):
    page_width: float | None = None
    page_height: float | None = None
    margin_top: float | None = None
    margin_bottom: float | None = None
    margin_left: float | None = None
    margin_right: float | None = None
    header: str | None = None
    footer: str | None = None
    default_font: FontFormat = Field(default_factory=FontFormat)


class HeadingNumbering(BaseModel):
    """Heading auto-numbering configuration.

    format types:
      - chinese_upper: 一、二、三...（一级）/（一）（二）...（二级）/ 1. 2. ...（三级）/（1）（2）...（四级）
      - chinese_lower: 一、二、三...（全部层级用中文数字，后缀不同）
      - decimal: 1. 1.1 1.1.1...（阿拉伯数字多级）
      - decimal_dot: 1、 1.1、...（中文顿号后缀）
    """
    enabled: bool = False
    format: str = "chinese_upper"  # chinese_upper | chinese_lower | decimal | decimal_dot
    levels: int = 4
    include_in_toc: bool = True


class TOCOptions(BaseModel):
    """Table of Contents generation options."""
    enabled: bool = False
    title: str = "目录"
    title_style: str = "Heading1"
    depth: int = 3
    show_page_numbers: bool = True
    leader: str = "dots"  # dots | solid | none
    new_page: bool = True


class PageNumberingFormat(str, Enum):
    DECIMAL = "decimal"  # 1, 2, 3...
    ROMAN_UPPER = "roman_upper"  # I, II, III...
    ROMAN_LOWER = "roman_lower"  # i, ii, iii...
    CHINESE = "chinese"  # 一、二、三...


class SectionConfig(BaseModel):
    """Configuration for a document section."""
    name: str
    page_numbering_enabled: bool = False
    page_numbering_format: PageNumberingFormat = PageNumberingFormat.DECIMAL
    page_numbering_start: int = 1
    header_text: str | None = None
    footer_text: str | None = None
    different_first_page: bool = False


class DocumentSections(BaseModel):
    """Section-based page numbering and header/footer configuration."""
    enabled: bool = False
    sections: list[SectionConfig] = Field(default_factory=list)
    # Section boundaries detected from document structure
    cover_has_header: bool = False
    toc_before_main: bool = True


class FormatRuleSet(BaseModel):
    """Unified format rules — output of both Method A and Method B."""
    document_level: DocumentLevel = Field(default_factory=DocumentLevel)
    styles: dict[str, StyleFormat] = Field(default_factory=dict)
    heading_numbering: HeadingNumbering = Field(default_factory=HeadingNumbering)
    toc: TOCOptions = Field(default_factory=TOCOptions)
    sections: DocumentSections = Field(default_factory=DocumentSections)
    sources: dict[str, str] = Field(default_factory=dict)


class ParagraphInfo(BaseModel):
    index: int
    text: str = ""
    style_name: str = "Normal"
    is_heading: bool = False
    heading_level: int = 0
    font: FontFormat = Field(default_factory=FontFormat)
    paragraph: ParagraphFormat = Field(default_factory=ParagraphFormat)


class TableInfo(BaseModel):
    rows: int = 0
    cols: int = 0
    cells: list[list[str]] = Field(default_factory=list)


class DocumentObject(BaseModel):
    """Parsed .docx content + format metadata."""
    paragraphs: list[ParagraphInfo] = Field(default_factory=list)
    tables: list[TableInfo] = Field(default_factory=list)
    page_width: float | None = None
    page_height: float | None = None
    margin_top: float | None = None
    margin_bottom: float | None = None
    margin_left: float | None = None
    margin_right: float | None = None
    header: str | None = None
    footer: str | None = None


class ChangeType(str, Enum):
    TYPO = "typo"
    TERM = "term"
    GRAMMAR = "grammar"
    FLUENCY = "fluency"


class TextChange(BaseModel):
    type: ChangeType
    original: str
    optimized: str
    explanation: str = ""


class ParagraphOptimization(BaseModel):
    index: int
    original_text: str
    optimized_text: str
    changes: list[TextChange] = Field(default_factory=list)


class OptimizationResult(BaseModel):
    paragraphs: list[ParagraphOptimization] = Field(default_factory=list)
    total_changes: int = 0
    by_type: dict[str, int] = Field(default_factory=dict)


class FormatSource(str, Enum):
    TEMPLATE = "template"
    TEXT_PARSE = "text_parse"
    PRESET = "preset"
    DEFAULT = "default"
    MANUAL = "manual"
