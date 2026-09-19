"""Router for format rule generation — Method A (template upload) and Method B (text input)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse

from src.modules.format_extractor import extract_format_rules
from src.modules.parser import parse_document
from src.modules.preset_templates import list_presets
from src.modules.requirement_parser import parse_requirement
from src.modules.textbox_extractor import extract_text_boxes

router = APIRouter(prefix="/api/rules", tags=["format-rules"])


def _convert_doc_to_docx(doc_path: str) -> str:
    """Convert .doc to .docx using Word COM automation."""
    import win32com.client
    
    docx_path = os.path.splitext(doc_path)[0] + ".docx"
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    try:
        doc = word.Documents.Open(doc_path, ReadOnly=True)
        doc.SaveAs2(docx_path, FileFormat=16)
        doc.Close(False)
    finally:
        word.Quit()
    return docx_path


@router.get("/presets")
def get_presets():
    return {"presets": list_presets()}


@router.post("/from-template")
async def rules_from_template(file: UploadFile = File(...)):
    """Method A — extract format rules from an uploaded template.
    
    Supports both .docx and .doc files. For .doc files, automatically converts
    to .docx first. Also detects text box annotations (批注类要求) and merges
    them with the template's own formatting.
    """
    if not file.filename:
        return JSONResponse(status_code=400, content={"error": "No filename provided"})

    lower_name = file.filename.lower()
    is_doc = lower_name.endswith(".doc")
    is_docx = lower_name.endswith(".docx")
    if not (is_doc or is_docx):
        return JSONResponse(status_code=400, content={"error": "Only .doc and .docx files are supported"})

    tmp_path: str | None = None
    docx_path: str | None = None
    try:
        suffix = ".doc" if is_doc else ".docx"
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(tmp_fd, "wb") as f:
            content = await file.read()
            f.write(content)

        # Convert .doc to .docx if needed
        if is_doc:
            try:
                docx_path = _convert_doc_to_docx(tmp_path)
            except Exception as exc:
                return JSONResponse(status_code=400, content={
                    "error": f"Failed to convert .doc to .docx: {exc}. Please save as .docx and try again."
                })
        else:
            docx_path = tmp_path

        doc_obj = parse_document(docx_path)
        rule_set = extract_format_rules(doc_obj, docx_path=docx_path)
        
        # Collect text box info for response
        text_boxes = extract_text_boxes(docx_path)
        format_boxes = [tb.text for tb in text_boxes if tb.text]

        return JSONResponse(content={
            "method": "template",
            "filename": file.filename,
            "file_format": "doc" if is_doc else "docx",
            "textbox_count": len(text_boxes),
            "has_textbox_requirements": len(format_boxes) > 0,
            "textbox_texts": format_boxes,
            "rule_set": json.loads(rule_set.model_dump_json()),
        })
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        if docx_path and docx_path != tmp_path and os.path.exists(docx_path):
            os.remove(docx_path)


@router.post("/from-preset")
async def rules_from_preset(
    preset_id: str = Form(...),
):
    """Use a preset template directly — no text input required."""
    from src.modules.preset_templates import get_preset_by_id
    
    try:
        preset = get_preset_by_id(preset_id)
        if preset is None:
            return JSONResponse(status_code=400, content={"error": f"Unknown preset: {preset_id}"})
        
        rule_set = preset["rule_set"]
        return JSONResponse(content={
            "method": "preset",
            "preset_id": preset_id,
            "preset_name": preset.get("name", preset_id),
            "rule_set": json.loads(rule_set.model_dump_json()),
        })
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})


@router.post("/from-text")
async def rules_from_text(
    text: str = Form(""),
    preset_id: str | None = Form(None),
):
    """Method B — parse natural-language format requirements into rules.
    
    If text is empty but preset_id is provided, uses the preset directly.
    If both are provided, merges the text requirements onto the preset.
    """
    try:
        # If no text but preset_id given, use preset directly
        if not text.strip() and preset_id:
            from src.modules.preset_templates import get_preset_by_id
            preset = get_preset_by_id(preset_id)
            if preset is None:
                return JSONResponse(status_code=400, content={"error": f"Unknown preset: {preset_id}"})
            rule_set = preset["rule_set"]
            return JSONResponse(content={
                "method": "preset",
                "preset_id": preset_id,
                "rule_set": json.loads(rule_set.model_dump_json()),
            })
        
        if not text.strip() and not preset_id:
            return JSONResponse(status_code=400, content={
                "error": "请输入格式要求文字或选择一个预设模板"
            })
        
        rule_set = parse_requirement(text, preset_id=preset_id)
        return JSONResponse(content={
            "method": "text_parse",
            "rule_set": json.loads(rule_set.model_dump_json()),
        })
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})
