from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from typing import Any
from app.parsers.ollama_cv_parser import OllamaCVParser
from app.utils.parsing_display import display_parsing_results
from pathlib import Path
import tempfile
import time
import uuid

router = APIRouter(prefix="/parse", tags=["parse"])

# Lazy singleton parser to avoid re-init per request
_parser: OllamaCVParser = None

def get_parser() -> OllamaCVParser:
    global _parser
    if _parser is None:
        _parser = OllamaCVParser()
    return _parser


@router.post("/upload")
async def upload_and_parse(file: UploadFile = File(...), background: bool = True, background_tasks: BackgroundTasks = None):
    """Upload a PDF and parse it.

    If background=True the task will be scheduled and a 202 returned with a "task_id".
    Otherwise the parsing will be done synchronously and the parsed document returned.
    """
    if file.content_type not in ("application/pdf",):
        raise HTTPException(status_code=400, detail="Only PDF uploads are accepted")

    tmp_dir = Path(tempfile.gettempdir()) / "piazzati_parsing"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    dest = tmp_dir / f"upload_{file.filename}_{int(time.time())}.pdf"
    content = await file.read()
    dest.write_bytes(content)

    parser = get_parser()

    if background:
        # schedule
        task_id = str(uuid.uuid4())
        def _bg():
            try:
                doc = parser.parse(str(dest))
                # persist doc somewhere or push to queue (TODO)
                print(f"Background parse finished: {task_id}")
            except Exception as e:
                print(f"Background parse failed: {e}")
        background_tasks.add_task(_bg)
        return JSONResponse(status_code=202, content={"task_id": task_id})
    else:
        doc = parser.parse(str(dest))
        text_summary = display_parsing_results(doc)
        return JSONResponse(status_code=200, content={"parsed": doc.model_dump(), "summary": text_summary})
