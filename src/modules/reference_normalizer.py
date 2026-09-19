"""Reference normalizer — converts bibliography entries to GB/T 7714-2015 format."""

from __future__ import annotations

import logging
import re
from typing import Any

from src.models import ChangeType, ParagraphOptimization, TextChange
from src.modules.llm_client import llm_client

logger = logging.getLogger(__name__)

_GB7714_SYSTEM = """你是一位文献著录格式专家，精通 GB/T 7714-2015《信息与文献 参考文献著录规则》。
请将用户给出的参考文献条目转换为标准的 GB/T 7714-2015 格式。

GB/T 7714-2015 核心规则：
1. 期刊论文[J]：作者. 题名[J]. 刊名, 年, 卷(期): 起止页码.
2. 专著[M]：作者. 书名[M]. 出版地: 出版社, 出版年.
3. 会议论文[C]：作者. 题名[C]//会议名称. 出版地: 出版社, 年: 页码.
4. 学位论文[D]：作者. 题名[D]. 保存地点: 保存单位, 年.
5. 标准[S]：责任者. 标准编号 标准名称[S]. 出版地: 出版者, 年.
6. 专利[P]：申请人. 专利名称: 专利号[P]. 公告日期.

详细要求：
- 中文文献：作者之间用逗号分隔，三个及以上只列前三个后加"等"
- 英文文献：作者姓在前名在后(缩写，不加缩写点)，三个及以上列前三个后加"et al"
- 题名首字母大写，其余小写（专有名词除外）；中文题名不加书名号
- 刊名/书名：中文用全称；英文实词首字母大写
- 年、卷、期之间用逗号分隔；期号放在括号内
- 页码前用冒号，起止页码用连字符(-)
- 文献类型标识必须加，放在题名后方括号内
- 条目末尾以英文句点(.)结尾
- 统一使用英文标点符号（逗号、句号、冒号、括号等）

请返回 JSON：
{
  "normalized_text": "标准化后的完整参考文献条目",
  "type": "J|M|C|D|S|P|R|N|DB",
  "changes": [
    {"type": "term", "original": "原文片段", "optimized": "修改后片段", "explanation": "修改原因(如：添加文献类型标识[J]、调整标点顺序等)"}
  ]
}
如果原文已经是标准格式，normalized_text 与原文相同，changes 为空数组。"""


def _looks_like_reference(text: str) -> bool:
    """Quick heuristic to check if a paragraph looks like a reference entry."""
    stripped = text.strip()
    if not stripped or len(stripped) < 15:
        return False
    # Has year pattern like 2024, 1999, etc.
    if not re.search(r'\b(19|20)\d{2}\b', stripped):
        return False
    # Has author-like pattern (Chinese names or Western names)
    if not re.search(r'[\u4e00-\u9fa5]+[,，.．]', stripped) and not re.search(r'[A-Z][a-z]+ [A-Z]', stripped):
        return False
    return True


def _rule_based_normalize(text: str) -> tuple[str, list[TextChange]]:
    """Basic rule-based normalization for degraded mode (no LLM).
    
    Handles the most common patterns with simple regex transformations.
    """
    original = text.strip()
    normalized = original
    changes: list[TextChange] = []

    # Pattern 1: Chinese journal with year, volume(issue): pages
    # 王立军，李华. 人工智能医疗应用的法律规制研究. 中国法学，2024，42(3): 55-72.
    m = re.match(
        r'^([^.]+)[.．]\s*([^.]+)[.．]\s*([^,，]+)[,，]\s*(\d{4})[,，]\s*(\d+)\((\d+)\)[:：]\s*(\d+[-\u2013]\d+)[.．]?$',
        original
    )
    if m:
        authors, title, journal, year, vol, issue, pages = m.groups()
        # Normalize: add [J], use English punctuation
        new = f"{authors}. {title}[J]. {journal}, {year}, {vol}({issue}): {pages}."
        if new != original:
            changes.append(TextChange(
                type=ChangeType.TERM,
                original=original,
                optimized=new,
                explanation="按照 GB/T 7714-2015 期刊格式标准化：添加[J]文献类型标识，统一英文标点",
            ))
            return new, changes

    # Pattern 2: Chinese monograph
    # 世界卫生组织. 人工智能在健康领域的伦理与治理指南. 日内瓦: 世界卫生组织出版社, 2023.
    m = re.match(
        r'^([^.]+)[.．]\s*([^.]+)[.．]\s*([^:：]+)[:：]\s*([^,，]+)[,，]\s*(\d{4})[.．]?$',
        original
    )
    if m:
        author, title, place, publisher, year = m.groups()
        # Check if it looks like a monograph (has place:publisher pattern)
        if any(kw in publisher for kw in ['出版社', '出版', 'Press', 'Publisher']):
            new = f"{author}. {title}[M]. {place}: {publisher}, {year}."
            if new != original:
                changes.append(TextChange(
                    type=ChangeType.TERM,
                    original=original,
                    optimized=new,
                    explanation="按照 GB/T 7714-2015 专著格式标准化：添加[M]文献类型标识",
                ))
                return new, changes

    # Pattern 3: English journal article
    # Smith J, Johnson K. Accountability and AI in clinical decision-making. Journal of ..., 2023, 49(2): 110-118.
    m = re.match(
        r'^([A-Z][a-zA-Z\s,]+[A-Z])[.．]\s*(.+?)[.．]\s*(.+?)[,，]\s*(\d{4})[,，]\s*(\d+)\((\d+)\)[:：]\s*(\d+[-\u2013]\d+)[.．]?$',
        original
    )
    if m:
        authors, title, journal, year, vol, issue, pages = m.groups()
        new = f"{authors}. {title}[J]. {journal}, {year}, {vol}({issue}): {pages}."
        if new != original:
            changes.append(TextChange(
                type=ChangeType.TERM,
                original=original,
                optimized=new,
                explanation="按照 GB/T 7714-2015 英文期刊格式标准化：添加[J]文献类型标识",
            ))
            return new, changes

    # General cleanup: normalize common Chinese punctuation patterns near year/volume
    # Replace Chinese commas between year/volume with English commas
    if re.search(r'\d{4}[，]\s*\d+\(', normalized):
        old = normalized
        normalized = re.sub(r'(\d{4})[，]\s*(\d+\()', r'\1, \2', normalized)
        if normalized != old:
            changes.append(TextChange(
                type=ChangeType.TYPO,
                original=old,
                optimized=normalized,
                explanation="年份与卷期之间统一使用英文逗号",
            ))

    return normalized, changes


def normalize_reference(text: str, para_index: int = 0) -> ParagraphOptimization:
    """Normalize a single reference entry to GB/T 7714-2015 format."""
    stripped = text.strip()
    if not stripped:
        return ParagraphOptimization(
            index=para_index,
            original_text=text,
            optimized_text=text,
        )

    # Start with rule-based normalization
    normalized, changes = _rule_based_normalize(stripped)

    # If LLM is available, use it for high-quality normalization
    if llm_client.available:
        try:
            raw = llm_client.chat_json(_GB7714_SYSTEM, stripped, temperature=0.1, max_tokens=4096)
            llm_normalized = raw.get("normalized_text", stripped)
            if llm_normalized and llm_normalized != stripped:
                llm_changes = []
                for ch in raw.get("changes", []):
                    try:
                        ct = ChangeType(ch.get("type", "term"))
                    except ValueError:
                        ct = ChangeType.TERM
                    llm_changes.append(
                        TextChange(
                            type=ct,
                            original=ch.get("original", ""),
                            optimized=ch.get("optimized", ""),
                            explanation=ch.get("explanation", ""),
                        )
                    )
                return ParagraphOptimization(
                    index=para_index,
                    original_text=text,
                    optimized_text=llm_normalized,
                    changes=llm_changes,
                )
        except Exception as exc:
            logger.error("LLM reference normalization failed for para %d: %s", para_index, exc)
            # Fall through to rule-based result

    return ParagraphOptimization(
        index=para_index,
        original_text=text,
        optimized_text=normalized if changes else text,
        changes=changes,
    )


def normalize_references(ref_paragraphs: list[Any]) -> list[ParagraphOptimization]:
    """Normalize a list of reference paragraphs.
    
    ref_paragraphs: list of ParagraphInfo or objects with .text and .index
    """
    results: list[ParagraphOptimization] = []
    for para in ref_paragraphs:
        if _looks_like_reference(para.text):
            results.append(normalize_reference(para.text, para.index))
        else:
            results.append(ParagraphOptimization(
                index=para.index,
                original_text=para.text,
                optimized_text=para.text,
            ))
    return results
