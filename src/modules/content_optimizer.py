"""Content optimizer — uses LLM to proofread and polish document text."""

from __future__ import annotations

import logging

from src.models import (
    ChangeType,
    DocumentObject,
    OptimizationResult,
    ParagraphInfo,
    ParagraphOptimization,
    TextChange,
)
from src.modules.llm_client import llm_client
from src.modules.reference_normalizer import normalize_reference

logger = logging.getLogger(__name__)

_OPTIMIZE_SYSTEM = """你是一位学术论文校对专家。请对用户给出的段落进行校对与优化，要求：
1. 纠正错别字和标点错误（type: "typo"）
2. 将口语化表达替换为学术规范用语（type: "term"）
3. 优化语句通顺度、消除语病，但不改变原意（type: "grammar" 或 "fluency"）
4. 保持专业术语的准确性和一致性
5. 中文语境下统一使用全角标点

请返回 JSON：
{
  "optimized_text": "优化后的完整段落文本",
  "changes": [
    {"type": "typo|term|grammar|fluency", "original": "原文片段", "optimized": "修改后片段", "explanation": "简短修改原因"}
  ]
}
如果没有修改，changes 为空数组，optimized_text 与原文相同。"""

_TYPO_ONLY_SYSTEM = """你是一位文字校对专家。请仅纠正以下文本中的错别字和标点错误，不要改变语句结构或用词。
请返回 JSON：
{
  "optimized_text": "校对后的文本",
  "changes": [
    {"type": "typo", "original": "原文片段", "optimized": "修改后片段", "explanation": "修改原因"}
  ]
}
如果没有错别字，changes 为空数组，optimized_text 与原文相同。"""

# Max chars per batch to LLM
_BATCH_SIZE = 2000


def _is_special_paragraph(para: ParagraphInfo) -> bool:
    """Headings, captions, references — only typo correction, no rewriting."""
    return para.is_heading or "caption" in para.style_name.lower() or "reference" in para.style_name.lower()


def _optimize_single(para: ParagraphInfo) -> ParagraphOptimization:
    text = para.text.strip()
    if not text:
        return ParagraphOptimization(
            index=para.index,
            original_text=para.text,
            optimized_text=para.text,
        )

    if not llm_client.available:
        return ParagraphOptimization(
            index=para.index,
            original_text=para.text,
            optimized_text=para.text,
        )

    system = _TYPO_ONLY_SYSTEM if _is_special_paragraph(para) else _OPTIMIZE_SYSTEM
    try:
        raw = llm_client.chat_json(system, text, temperature=0.2, max_tokens=4096)
        optimized = raw.get("optimized_text", text)
        changes = []
        for ch in raw.get("changes", []):
            try:
                ct = ChangeType(ch.get("type", "fluency"))
            except ValueError:
                ct = ChangeType.FLUENCY
            changes.append(
                TextChange(
                    type=ct,
                    original=ch.get("original", ""),
                    optimized=ch.get("optimized", ""),
                    explanation=ch.get("explanation", ""),
                )
            )
        return ParagraphOptimization(
            index=para.index,
            original_text=para.text,
            optimized_text=optimized,
            changes=changes,
        )
    except Exception as exc:
        logger.error("LLM optimization failed for paragraph %d: %s", para.index, exc)
        return ParagraphOptimization(
            index=para.index,
            original_text=para.text,
            optimized_text=para.text,
        )


def optimize_content(doc_obj: DocumentObject) -> OptimizationResult:
    """Optimize all paragraphs in a DocumentObject. Returns OptimizationResult.
    
    Reference entries in the references section are normalized to GB/T 7714-2015 format.
    """
    results: list[ParagraphOptimization] = []
    in_ref_section = False
    ref_keywords = {"参考文献", "参考资料", "references", "bibliography"}

    for para in doc_obj.paragraphs:
        stripped = para.text.strip()

        # Track references section
        if stripped in ref_keywords:
            in_ref_section = True
            # The heading itself only gets typo correction
            results.append(_optimize_single(para))
            continue
        elif in_ref_section and para.is_heading and stripped:
            in_ref_section = False

        # References section: normalize entries to GB/T 7714
        if in_ref_section and stripped and not para.is_heading:
            results.append(normalize_reference(para.text, para.index))
            continue

        results.append(_optimize_single(para))

    # Aggregate stats
    total_changes = sum(len(r.changes) for r in results)
    by_type: dict[str, int] = {}
    for r in results:
        for ch in r.changes:
            by_type[ch.type.value] = by_type.get(ch.type.value, 0) + 1

    return OptimizationResult(
        paragraphs=results,
        total_changes=total_changes,
        by_type=by_type,
    )
