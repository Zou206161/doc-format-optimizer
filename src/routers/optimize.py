"""Router for content optimization and final document generation."""

from __future__ import annotations

import json
import os
import tempfile

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse, FileResponse

from src.models import FormatRuleSet
from src.modules.content_optimizer import optimize_content
from src.modules.doc_generator import generate_document
from src.modules.format_applier import apply_format
from src.modules.parser import parse_document

router = APIRouter(prefix="/api/optimize", tags=["optimize"])


@router.post("/preview")
async def preview_optimization(file: UploadFile = File(...)):
    """Upload a draft .docx, return optimization preview without generating the final file."""
    if not file.filename or not file.filename.endswith(".docx"):
        return JSONResponse(status_code=400, content={"error": "Only .docx files are supported"})

    tmp_path: str | None = None
    try:
        suffix = os.path.splitext(file.filename)[1]
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(tmp_fd, "wb") as f:
            content = await file.read()
            f.write(content)

        doc_obj = parse_document(tmp_path)
        result = optimize_content(doc_obj)

        return JSONResponse(content=json.loads(result.model_dump_json()))
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/generate")
async def generate_final(
    file: UploadFile = File(...),
    rules_json: str = Form(...),
    skip_optimization: bool = Form(False),
):
    """Full pipeline: parse draft → optimize content → apply rules → generate .docx."""
    if not file.filename or not file.filename.endswith(".docx"):
        return JSONResponse(status_code=400, content={"error": "Only .docx files are supported"})

    tmp_path: str | None = None
    out_path: str | None = None
    try:
        rule_set = FormatRuleSet.model_validate_json(rules_json)
    except Exception as exc:
        return JSONResponse(status_code=422, content={"error": f"Invalid rules JSON: {exc}"})

    try:
        suffix = os.path.splitext(file.filename)[1]
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(tmp_fd, "wb") as f:
            content = await file.read()
            f.write(content)

        doc_obj = parse_document(tmp_path)

        opt_result = None if skip_optimization else optimize_content(doc_obj)

        formatted = apply_format(doc_obj, opt_result, rule_set)

        out_fd, out_path = tempfile.mkstemp(suffix=".docx")
        os.close(out_fd)
        generate_document(formatted, out_path)

        return FileResponse(
            out_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="成品.docx",
        )
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
