"""Heading auto-numbering module — generates numbering for heading paragraphs.

Supports multiple numbering formats:
  - chinese_upper: 一、/（一）/ 1. /（1）/ ① (混合格式，学术论文标准)
  - chinese_lower: 一、/（一）/ 1、/（1） (全中文格式)
  - decimal: 1. / 1.1 / 1.1.1 / 1.1.1.1 (阿拉伯数字多级)
  - decimal_dot: 1、/ 1.1、/ 1.1.1、 (阿拉伯数字+顿号)
"""

from __future__ import annotations

import logging

from src.models import HeadingNumbering

logger = logging.getLogger(__name__)

# Chinese number mapping (1-99)
_CN_NUM = [
    "", "一", "二", "三", "四", "五", "六", "七", "八", "九",
    "十", "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九",
    "二十", "二十一", "二十二", "二十三", "二十四", "二十五", "二十六", "二十七", "二十八", "二十九",
    "三十", "三十一", "三十二", "三十三", "三十四", "三十五", "三十六", "三十七", "三十八", "三十九",
    "四十", "四十一", "四十二", "四十三", "四十四", "四十五", "四十六", "四十七", "四十八", "四十九",
    "五十", "五十一", "五十二", "五十三", "五十四", "五十五", "五十六", "五十七", "五十八", "五十九",
    "六十", "六十一", "六十二", "六十三", "六十四", "六十五", "六十六", "六十七", "六十八", "六十九",
    "七十", "七十一", "七十二", "七十三", "七十四", "七十五", "七十六", "七十七", "七十八", "七十九",
    "八十", "八十一", "八十二", "八十三", "八十四", "八十五", "八十六", "八十七", "八十八", "八十九",
    "九十", "九十一", "九十二", "九十三", "九十四", "九十五", "九十六", "九十七", "九十八", "九十九",
]


def _to_chinese(n: int) -> str:
    """Convert integer (1-99) to Chinese number."""
    if n <= 0 or n > 99:
        return str(n)
    return _CN_NUM[n]


def _to_roman(n: int, upper: bool = True) -> str:
    """Convert integer to Roman numeral."""
    vals = [
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    ]
    result = ""
    for val, sym in vals:
        while n >= val:
            result += sym
            n -= val
    return result if upper else result.lower()


def _chinese_upper_number(counters: list[int], level: int) -> str:
    """Standard Chinese academic numbering format.

    Level 1: 一、二、三、
    Level 2: （一）（二）（三）
    Level 3: 1. 2. 3.
    Level 4: （1）（2）（3）
    Level 5: ① ② ③
    """
    idx = counters[level - 1] if level <= len(counters) else 1
    if level == 1:
        return f"{_to_chinese(idx)}、"
    elif level == 2:
        return f"（{_to_chinese(idx)}）"
    elif level == 3:
        return f"{idx}."
    elif level == 4:
        return f"（{idx}）"
    else:
        return f"({idx})"


def _chinese_lower_number(counters: list[int], level: int) -> str:
    """All levels use Chinese numbers with different suffixes."""
    idx = counters[level - 1] if level <= len(counters) else 1
    cn = _to_chinese(idx)
    if level == 1:
        return f"{cn}、"
    elif level == 2:
        return f"（{cn}）"
    elif level == 3:
        return f"{cn}、"
    else:
        return f"（{cn}）"


def _decimal_number(counters: list[int], level: int) -> str:
    """1. / 1.1 / 1.1.1 / 1.1.1.1"""
    parts = [str(counters[i]) for i in range(min(level, len(counters)))]
    return ".".join(parts) + "."


def _decimal_dot_number(counters: list[int], level: int) -> str:
    """1、/ 1.1、/ 1.1.1、"""
    parts = [str(counters[i]) for i in range(min(level, len(counters)))]
    return ".".join(parts) + "、"


_NUMBER_FUNCTIONS = {
    "chinese_upper": _chinese_upper_number,
    "chinese_lower": _chinese_lower_number,
    "decimal": _decimal_number,
    "decimal_dot": _decimal_dot_number,
}


def generate_heading_number(counters: list[int], level: int, fmt: str = "chinese_upper") -> str:
    """Generate a heading number string from counters.

    Args:
        counters: list of current counts per level (index 0 = level 1)
        level: heading level (1-based)
        fmt: numbering format name

    Returns:
        Formatted number string (e.g. "一、", "1.1、", "（二）")
    """
    func = _NUMBER_FUNCTIONS.get(fmt, _chinese_upper_number)
    return func(counters, level)


def apply_heading_numbers(
    paragraphs: list,
    numbering: HeadingNumbering,
) -> list:
    """Apply auto-numbering to heading paragraphs.

    Modifies the text of heading paragraphs by prepending the number.
    Non-heading paragraphs are unchanged.

    Args:
        paragraphs: list of paragraph dicts/objects with .text, .is_heading, .heading_level
        numbering: HeadingNumbering configuration

    Returns:
        New list of paragraphs with numbering applied.
    """
    if not numbering.enabled:
        return paragraphs

    max_level = numbering.levels
    counters = [0] * max_level
    fmt = numbering.format
    result = []

    for para in paragraphs:
        if hasattr(para, "is_heading"):
            is_heading = para.is_heading
            level = para.heading_level or 1
            text = para.text
            style_key = getattr(para, "style_key", "")
        elif isinstance(para, dict):
            is_heading = para.get("is_heading", False)
            level = para.get("heading_level", 1) or 1
            text = para.get("text", "")
            style_key = para.get("style_key", "")
        else:
            result.append(para)
            continue

        # Skip Title style — it's the document title, not a numbered heading
        if style_key == "Title":
            result.append(para)
            continue

        if is_heading and 1 <= level <= max_level and text.strip():
            # Increment counter for this level, reset lower levels
            counters[level - 1] += 1
            for i in range(level, max_level):
                counters[i] = 0

            number_str = generate_heading_number(counters, level, fmt)
            new_text = number_str + text.lstrip()

            # Create updated copy
            new_para = para.model_copy(update={"text": new_text}) if hasattr(para, "model_copy") else None
            if new_para is None and isinstance(para, dict):
                new_para = {**para, "text": new_text}
            elif new_para is None:
                new_para = para
                if hasattr(para, "text"):
                    para.text = new_text
                new_para = para
            result.append(new_para)
        else:
            result.append(para)

    return result
