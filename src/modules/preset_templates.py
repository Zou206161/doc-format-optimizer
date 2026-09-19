"""Built-in preset format templates based on Chinese national standards.

References:
- GB/T 7713.1-2006/2025 《学位论文编写规则》
- GB/T 7714-2015 《参考文献著录规则》
- Common university thesis format guidelines

Key conversions:
- 1cm = 28.35pt
- Chinese font sizes: 二号=22pt, 小二=18pt, 三号=16pt, 四号=14pt,
  小四=12pt, 五号=10.5pt, 小五=9pt
"""

from __future__ import annotations

from src.models import (
    Alignment,
    DocumentLevel,
    DocumentSections,
    FontFormat,
    FormatRuleSet,
    HeadingNumbering,
    PageNumberingFormat,
    ParagraphFormat,
    SectionConfig,
    StyleFormat,
    TOCOptions,
)

# Unit conversion
CM = 28.35  # 1cm = 28.35pt


def _build_undergraduate_thesis() -> FormatRuleSet:
    """本科毕业论文 — 基于多所大学本科论文格式常见标准。

    页边距: 上2.5cm 下2.5cm 左3cm(装订) 右2cm
    字体: 大标题二号黑体, H1三号黑体, H2四号黑体, H3小四黑体, 正文小四宋体
    行距: 1.5倍, 首行缩进2字符
    参考文献: 五号宋体, GB/T 7714格式
    """
    return FormatRuleSet(
        document_level=DocumentLevel(
            page_width=595.3,
            page_height=841.9,
            margin_top=2.5 * CM,       # 70.88pt = 2.5cm
            margin_bottom=2.5 * CM,    # 70.88pt = 2.5cm
            margin_left=3.0 * CM,      # 85.05pt = 3cm (装订侧)
            margin_right=2.0 * CM,     # 56.69pt = 2cm
            header="本科毕业论文",
            default_font=FontFormat(
                font_name="Times New Roman",
                font_name_east_asia="宋体",
                font_size=12.0,  # 小四
            ),
        ),
        styles={
            "Title": StyleFormat(
                font=FontFormat(
                    font_name="黑体",
                    font_name_east_asia="黑体",
                    font_size=22.0,  # 二号
                    bold=True,
                ),
                paragraph=ParagraphFormat(
                    alignment=Alignment.CENTER,
                    space_before=24.0,
                    space_after=18.0,
                ),
            ),
            "Heading1": StyleFormat(
                font=FontFormat(
                    font_name="黑体",
                    font_name_east_asia="黑体",
                    font_size=16.0,  # 三号
                    bold=True,
                ),
                paragraph=ParagraphFormat(
                    alignment=Alignment.CENTER,
                    space_before=24.0,
                    space_after=18.0,
                ),
            ),
            "Heading2": StyleFormat(
                font=FontFormat(
                    font_name="黑体",
                    font_name_east_asia="黑体",
                    font_size=14.0,  # 四号
                    bold=True,
                ),
                paragraph=ParagraphFormat(
                    alignment=Alignment.LEFT,
                    space_before=18.0,
                    space_after=12.0,
                ),
            ),
            "Heading3": StyleFormat(
                font=FontFormat(
                    font_name="黑体",
                    font_name_east_asia="黑体",
                    font_size=12.0,  # 小四
                    bold=True,
                ),
                paragraph=ParagraphFormat(
                    alignment=Alignment.LEFT,
                    space_before=12.0,
                    space_after=6.0,
                ),
            ),
            "Body": StyleFormat(
                font=FontFormat(
                    font_name="Times New Roman",
                    font_name_east_asia="宋体",
                    font_size=12.0,  # 小四
                ),
                paragraph=ParagraphFormat(
                    alignment=Alignment.JUSTIFY,
                    line_spacing=1.5,
                    line_spacing_rule="multiple",
                    first_line_indent=24.0,  # 2字符
                    space_before=0.0,
                    space_after=0.0,
                ),
            ),
            "Caption": StyleFormat(
                font=FontFormat(
                    font_name="Times New Roman",
                    font_name_east_asia="宋体",
                    font_size=10.5,  # 五号
                ),
                paragraph=ParagraphFormat(
                    alignment=Alignment.CENTER,
                    space_before=6.0,
                    space_after=6.0,
                ),
            ),
            "Reference": StyleFormat(
                font=FontFormat(
                    font_name="Times New Roman",
                    font_name_east_asia="宋体",
                    font_size=10.5,  # 五号
                ),
                paragraph=ParagraphFormat(
                    alignment=Alignment.JUSTIFY,
                    line_spacing=1.5,
                    line_spacing_rule="multiple",
                    first_line_indent=0.0,
                    left_indent=24.0,  # 悬挂缩进2字符
                    space_before=0.0,
                    space_after=0.0,
                ),
            ),
        },
        heading_numbering=HeadingNumbering(
            enabled=True,
            format="chinese_upper",
            levels=4,
            include_in_toc=True,
        ),
        toc=TOCOptions(
            enabled=False,
            title="目录",
            title_style="Heading1",
            depth=3,
            show_page_numbers=True,
            leader="dots",
            new_page=True,
        ),
        sections=DocumentSections(
            enabled=False,
            sections=[
                SectionConfig(
                    name="front_matter",
                    page_numbering_enabled=True,
                    page_numbering_format=PageNumberingFormat.ROMAN_LOWER,
                    page_numbering_start=1,
                    header_text="本科毕业论文",
                ),
                SectionConfig(
                    name="main",
                    page_numbering_enabled=True,
                    page_numbering_format=PageNumberingFormat.DECIMAL,
                    page_numbering_start=1,
                    header_text="本科毕业论文",
                ),
            ],
        ),
    )


def _build_master_thesis() -> FormatRuleSet:
    """硕士学位论文 — 基于GB/T 7713.1及重点大学硕论格式规范。

    页边距: 天头25mm 地角20mm 订口25mm 切口20mm (GB/T 7713.1版面留白要求)
    字体: 大标题小二黑体, H1三号黑体, H2四号黑体, H3小四黑体, 正文小四宋体
    行距: 固定值20磅, 首行缩进2字符
    参考文献: 五号宋体, GB/T 7714格式
    """
    return FormatRuleSet(
        document_level=DocumentLevel(
            page_width=595.3,
            page_height=841.9,
            margin_top=2.5 * CM,       # 天头25mm = 70.88pt
            margin_bottom=2.0 * CM,   # 地角20mm = 56.69pt
            margin_left=2.5 * CM,      # 订口25mm = 70.88pt
            margin_right=2.0 * CM,     # 切口20mm = 56.69pt
            header="硕士学位论文",
            default_font=FontFormat(
                font_name="Times New Roman",
                font_name_east_asia="宋体",
                font_size=12.0,  # 小四
            ),
        ),
        styles={
            "Title": StyleFormat(
                font=FontFormat(
                    font_name="黑体",
                    font_name_east_asia="黑体",
                    font_size=18.0,  # 小二
                    bold=True,
                ),
                paragraph=ParagraphFormat(
                    alignment=Alignment.CENTER,
                    space_before=24.0,
                    space_after=18.0,
                ),
            ),
            "Heading1": StyleFormat(
                font=FontFormat(
                    font_name="黑体",
                    font_name_east_asia="黑体",
                    font_size=16.0,  # 三号
                    bold=True,
                ),
                paragraph=ParagraphFormat(
                    alignment=Alignment.CENTER,
                    space_before=24.0,
                    space_after=18.0,
                ),
            ),
            "Heading2": StyleFormat(
                font=FontFormat(
                    font_name="黑体",
                    font_name_east_asia="黑体",
                    font_size=14.0,  # 四号
                    bold=True,
                ),
                paragraph=ParagraphFormat(
                    alignment=Alignment.LEFT,
                    space_before=18.0,
                    space_after=12.0,
                ),
            ),
            "Heading3": StyleFormat(
                font=FontFormat(
                    font_name="黑体",
                    font_name_east_asia="黑体",
                    font_size=12.0,  # 小四
                    bold=True,
                ),
                paragraph=ParagraphFormat(
                    alignment=Alignment.LEFT,
                    space_before=12.0,
                    space_after=6.0,
                ),
            ),
            "Body": StyleFormat(
                font=FontFormat(
                    font_name="Times New Roman",
                    font_name_east_asia="宋体",
                    font_size=12.0,  # 小四
                ),
                paragraph=ParagraphFormat(
                    alignment=Alignment.JUSTIFY,
                    line_spacing=20.0,       # 固定值20磅
                    line_spacing_rule="exact",
                    first_line_indent=24.0, # 2字符
                    space_before=0.0,
                    space_after=0.0,
                ),
            ),
            "Caption": StyleFormat(
                font=FontFormat(
                    font_name="Times New Roman",
                    font_name_east_asia="宋体",
                    font_size=10.5,  # 五号
                ),
                paragraph=ParagraphFormat(
                    alignment=Alignment.CENTER,
                    space_before=6.0,
                    space_after=6.0,
                ),
            ),
            "Reference": StyleFormat(
                font=FontFormat(
                    font_name="Times New Roman",
                    font_name_east_asia="宋体",
                    font_size=10.5,  # 五号
                ),
                paragraph=ParagraphFormat(
                    alignment=Alignment.JUSTIFY,
                    line_spacing=1.5,
                    line_spacing_rule="multiple",
                    first_line_indent=0.0,
                    left_indent=24.0,  # 悬挂缩进
                    space_before=0.0,
                    space_after=0.0,
                ),
            ),
        },
        heading_numbering=HeadingNumbering(
            enabled=True,
            format="decimal",
            levels=4,
            include_in_toc=True,
        ),
        toc=TOCOptions(
            enabled=False,
            title="目录",
            title_style="Heading1",
            depth=3,
            show_page_numbers=True,
            leader="dots",
            new_page=True,
        ),
        sections=DocumentSections(
            enabled=False,
            sections=[
                SectionConfig(
                    name="front_matter",
                    page_numbering_enabled=True,
                    page_numbering_format=PageNumberingFormat.ROMAN_LOWER,
                    page_numbering_start=1,
                    header_text="硕士学位论文",
                ),
                SectionConfig(
                    name="main",
                    page_numbering_enabled=True,
                    page_numbering_format=PageNumberingFormat.DECIMAL,
                    page_numbering_start=1,
                    header_text="硕士学位论文",
                ),
            ],
        ),
    )


def _build_journal_article() -> FormatRuleSet:
    """期刊投稿 — 基于常见中文期刊投稿格式规范。

    页边距: 四周2.5cm
    字体: 标题三号黑体, H1四号黑体, H2小四黑体, 正文五号宋体
    行距: 单倍行距, 首行缩进2字符
    参考文献: 小五宋体, GB/T 7714格式
    """
    return FormatRuleSet(
        document_level=DocumentLevel(
            page_width=595.3,
            page_height=841.9,
            margin_top=2.5 * CM,
            margin_bottom=2.5 * CM,
            margin_left=2.5 * CM,
            margin_right=2.5 * CM,
            default_font=FontFormat(
                font_name="Times New Roman",
                font_name_east_asia="宋体",
                font_size=10.5,  # 五号
            ),
        ),
        styles={
            "Title": StyleFormat(
                font=FontFormat(
                    font_name="黑体",
                    font_name_east_asia="黑体",
                    font_size=16.0,  # 三号
                    bold=True,
                ),
                paragraph=ParagraphFormat(
                    alignment=Alignment.CENTER,
                    space_before=12.0,
                    space_after=12.0,
                ),
            ),
            "Heading1": StyleFormat(
                font=FontFormat(
                    font_name="黑体",
                    font_name_east_asia="黑体",
                    font_size=14.0,  # 四号
                    bold=True,
                ),
                paragraph=ParagraphFormat(
                    alignment=Alignment.LEFT,
                    space_before=12.0,
                    space_after=6.0,
                ),
            ),
            "Heading2": StyleFormat(
                font=FontFormat(
                    font_name="黑体",
                    font_name_east_asia="黑体",
                    font_size=12.0,  # 小四
                    bold=True,
                ),
                paragraph=ParagraphFormat(
                    alignment=Alignment.LEFT,
                    space_before=10.0,
                    space_after=5.0,
                ),
            ),
            "Body": StyleFormat(
                font=FontFormat(
                    font_name="Times New Roman",
                    font_name_east_asia="宋体",
                    font_size=10.5,  # 五号
                ),
                paragraph=ParagraphFormat(
                    alignment=Alignment.JUSTIFY,
                    line_spacing=1.0,  # 单倍
                    line_spacing_rule="multiple",
                    first_line_indent=21.0,  # 2字符(10.5pt×2)
                    space_before=0.0,
                    space_after=0.0,
                ),
            ),
            "Caption": StyleFormat(
                font=FontFormat(
                    font_name="Times New Roman",
                    font_name_east_asia="宋体",
                    font_size=9.0,  # 小五
                ),
                paragraph=ParagraphFormat(
                    alignment=Alignment.CENTER,
                    space_before=3.0,
                    space_after=3.0,
                ),
            ),
            "Reference": StyleFormat(
                font=FontFormat(
                    font_name="Times New Roman",
                    font_name_east_asia="宋体",
                    font_size=9.0,  # 小五
                ),
                paragraph=ParagraphFormat(
                    alignment=Alignment.JUSTIFY,
                    line_spacing=1.0,
                    line_spacing_rule="multiple",
                    first_line_indent=0.0,
                    left_indent=21.0,  # 悬挂缩进2字符
                    space_before=0.0,
                    space_after=0.0,
                ),
            ),
        },
        heading_numbering=HeadingNumbering(
            enabled=True,
            format="decimal",
            levels=3,
            include_in_toc=True,
        ),
        toc=TOCOptions(
            enabled=False,
            title="目录",
            title_style="Heading1",
            depth=2,
            show_page_numbers=True,
            leader="dots",
            new_page=False,
        ),
        sections=DocumentSections(
            enabled=False,
            sections=[],
        ),
    )


def _build_doctoral_thesis() -> FormatRuleSet:
    """博士学位论文 — 基于GB/T 7713.1及重点大学博论格式规范。

    页边距: 天头25mm 地角20mm 订口25mm 切口20mm
    字体: 大标题二号黑体, H1三号黑体, H2四号黑体, H3小四黑体, 正文小四宋体
    行距: 固定值22磅, 首行缩进2字符
    参考文献: 五号宋体, GB/T 7714格式
    """
    rules = _build_master_thesis()
    # 博士论文: 大标题用二号(22pt), 行距22磅
    rules.styles["Title"].font.font_size = 22.0  # 二号
    rules.styles["Body"].paragraph.line_spacing = 22.0  # 固定22磅
    rules.document_level.header = "博士学位论文"
    return rules


PRESET_TEMPLATES: list[dict] = [
    {
        "id": "undergraduate_thesis",
        "name": "本科毕业论文",
        "keywords": ["本科", "毕业论文", "学士", "毕设", "本科生"],
        "description": "基于多所大学本科论文格式常见标准：A4纸，左3cm装订，二号黑体标题，小四宋体正文，1.5倍行距",
        "rule_set": _build_undergraduate_thesis(),
    },
    {
        "id": "master_thesis",
        "name": "硕士学位论文",
        "keywords": ["硕士", "学位论文", "研究生", "硕论", "硕士学位"],
        "description": "基于GB/T 7713.1标准：A4纸，天头25mm/地角20mm，小二黑体标题，小四宋体正文，固定20磅行距",
        "rule_set": _build_master_thesis(),
    },
    {
        "id": "doctoral_thesis",
        "name": "博士学位论文",
        "keywords": ["博士", "博士学位", "博论", "博士论文"],
        "description": "基于GB/T 7713.1标准：A4纸，二号黑体标题，小四宋体正文，固定22磅行距",
        "rule_set": _build_doctoral_thesis(),
    },
    {
        "id": "journal_article",
        "name": "期刊投稿",
        "keywords": ["期刊", "投稿", "论文发表", "学报", "杂志"],
        "description": "基于常见中文期刊格式：A4纸，四周2.5cm边距，三号黑体标题，五号宋体正文，单倍行距",
        "rule_set": _build_journal_article(),
    },
]


def match_preset(text: str) -> dict | None:
    """Match user text against preset template keywords. Returns the first hit or None."""
    for preset in PRESET_TEMPLATES:
        for kw in preset["keywords"]:
            if kw in text:
                return preset
    return None


def list_presets() -> list[dict]:
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "description": p.get("description", ""),
        }
        for p in PRESET_TEMPLATES
    ]


def get_preset_by_id(preset_id: str) -> dict | None:
    for p in PRESET_TEMPLATES:
        if p["id"] == preset_id:
            return p
    return None
