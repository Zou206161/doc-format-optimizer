"""Text box extractor — extracts text boxes from .docx files.

Text boxes in Word documents often contain format requirements / annotations
that describe how the document should be formatted. This module extracts
all text box content so it can be parsed as format requirements.
"""

from __future__ import annotations

import logging
from typing import NamedTuple

from docx import Document
from lxml import etree

logger = logging.getLogger(__name__)

# XML namespaces for Word Open XML
_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_WPS_NS = "http://schemas.microsoft.com/office/word/2010/wordprocessingShape"
_MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
_V_NS = "urn:schemas-microsoft-com:vml"
_A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


class TextBoxContent(NamedTuple):
    """A single text box's content and metadata."""
    index: int
    text: str
    paragraph_index: int | None  # Nearby paragraph index, if determinable


def extract_text_boxes(docx_path: str) -> list[TextBoxContent]:
    """Extract all text box content from a .docx file.

    Text boxes can be in two formats:
    1. WPS (WordprocessingShape) — modern text boxes in DrawingML
    2. VML (Vector Markup Language) — legacy text boxes from .doc conversion

    Returns a list of TextBoxContent objects.
    """
    doc = Document(docx_path)
    body = doc.element.body
    results: list[TextBoxContent] = []

    # Method 1: WPS text boxes (wps:txbxContent)
    wps_boxes = body.findall(f".//{{{_WPS_NS}}}txbxContent")
    for idx, tb in enumerate(wps_boxes):
        texts = tb.findall(f".//{{{_W_NS}}}t")
        full_text = "".join(t.text or "" for t in texts).strip()
        if full_text:
            # Try to find the nearby paragraph index
            para_idx = _find_nearby_paragraph_index(body, tb)
            results.append(TextBoxContent(
                index=idx,
                text=full_text,
                paragraph_index=para_idx,
            ))

    # Method 2: VML text boxes (v:textbox) — legacy format
    vml_boxes = body.findall(f".//{{{_V_NS}}}textbox")
    for idx, tb in enumerate(vml_boxes):
        # VML textbox content is in w:txbxContent inside the v:textbox
        texts = tb.findall(f".//{{{_W_NS}}}t")
        full_text = "".join(t.text or "" for t in texts).strip()
        if full_text:
            # Avoid duplicates with WPS boxes
            if full_text not in [r.text for r in results]:
                para_idx = _find_nearby_paragraph_index(body, tb)
                results.append(TextBoxContent(
                    index=len(results),
                    text=full_text,
                    paragraph_index=para_idx,
                ))

    logger.info("Extracted %d text boxes from %s", len(results), docx_path)
    return results


def _find_nearby_paragraph_index(body, element) -> int | None:
    """Try to find the paragraph index that contains or is near a text box element."""
    # Walk up the tree to find the containing paragraph
    parent = element.getparent()
    while parent is not None and parent.tag != f"{{{_W_NS}}}p":
        parent = parent.getparent()
    
    if parent is None:
        return None
    
    # Count paragraphs before this one
    paragraphs = body.findall(f".//{{{_W_NS}}}p")
    for i, p in enumerate(paragraphs):
        if p is parent:
            return i
    return None


def has_text_boxes(docx_path: str) -> bool:
    """Check if a .docx file contains text boxes with content."""
    boxes = extract_text_boxes(docx_path)
    return len(boxes) > 0


def get_text_box_texts(docx_path: str) -> list[str]:
    """Simple helper: return just the text content of all text boxes."""
    return [tb.text for tb in extract_text_boxes(docx_path)]
