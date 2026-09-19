"""Chinese font size name to point (pt) value mapping."""

CHINESE_FONT_SIZE_MAP = {
    "初号": 42.0,
    "小初": 36.0,
    "一号": 26.0,
    "小一": 24.0,
    "二号": 22.0,
    "小二": 18.0,
    "三号": 16.0,
    "小三": 15.0,
    "四号": 14.0,
    "小四": 12.0,
    "五号": 10.5,
    "小五": 9.0,
    "六号": 7.5,
    "小六": 6.5,
    "七号": 5.5,
    "八号": 5.0,
}

PT_PER_CM = 28.35
PT_PER_INCH = 72.0


def chinese_size_to_pt(name: str) -> float | None:
    """Convert a Chinese font size name (e.g. '小四') to points (e.g. 12.0)."""
    return CHINESE_FONT_SIZE_MAP.get(name.strip())


def cm_to_pt(cm: float) -> float:
    return round(cm * PT_PER_CM, 2)


def inch_to_pt(inch: float) -> float:
    return round(inch * PT_PER_INCH, 2)


def parse_font_size(text: str) -> float | None:
    """Try every known notation to resolve a font-size string to pt."""
    text = text.strip()
    direct = chinese_size_to_pt(text)
    if direct is not None:
        return direct
    lower = text.lower()
    for unit, factor in [("pt", 1.0), ("px", 0.75), ("cm", PT_PER_CM), ("mm", PT_PER_CM / 10)]:
        if lower.endswith(unit):
            try:
                return round(float(lower[: -len(unit)]) * factor, 2)
            except ValueError:
                pass
    try:
        return round(float(text), 2)
    except ValueError:
        return None


def chars_to_pt(num_chars: float, font_size_pt: float) -> float:
    """Convert character-width-based indent to pt (1 char = current font size in pt)."""
    return round(num_chars * font_size_pt, 2)
