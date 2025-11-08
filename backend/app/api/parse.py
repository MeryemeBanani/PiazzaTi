import tempfile
import time
import uuid
from pathlib import Path

from ..parsers.ollama_cv_parser import OllamaCVParser
from ..utils.parsing_display import display_parsing_results
from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    UploadFile,
)
import json
import importlib.util
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

router = APIRouter(prefix="/parse", tags=["parse"])


# Lazy singleton parser to avoid re-init per request
_parser: OllamaCVParser = None


def get_parser() -> OllamaCVParser:
    global _parser
    if _parser is None:
        _parser = OllamaCVParser()
    return _parser


@router.get("/status")
async def get_parser_status():
    """Check parser and LLM status."""
    parser = get_parser()
    
    llm_status = {
        "llm_available": hasattr(parser, 'llm') and parser.llm is not None,
        "base_url": getattr(parser, 'base_url', 'unknown'),
        "model": getattr(parser, 'model', 'unknown')
    }
    
    # Test Ollama connectivity
    try:
        from ..ollama_integration import check_ollama_api
        ollama_reachable = check_ollama_api(timeout=3)
        llm_status["ollama_reachable"] = ollama_reachable
    except Exception as e:
        llm_status["ollama_reachable"] = False
        llm_status["ollama_error"] = str(e)
    
    return {
        "parser_initialized": parser is not None,
        "parser_version": "v1.7.4 FINAL",
        "llm_status": llm_status
    }


@router.post("/reinitialize-llm")
async def reinitialize_llm(base_url: str = "http://host.docker.internal:11434"):
    """Reinitialize LLM with new base_url."""
    global _parser
    
    try:
        # Create new parser instance with updated base_url
        _parser = OllamaCVParser(base_url=base_url)
        
        status = {
            "success": True,
            "llm_available": hasattr(_parser, 'llm') and _parser.llm is not None,
            "base_url": _parser.base_url,
            "model": _parser.model
        }
        
        if status["llm_available"]:
            status["message"] = "LLM successfully reinitialized and connected!"
        else:
            status["message"] = "Parser reinitialized but LLM connection failed"
            
        return status
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to reinitialize LLM"
        }


MULTIPART_AVAILABLE = importlib.util.find_spec("multipart") is not None


if MULTIPART_AVAILABLE:
    @router.post("/upload")
    async def upload_and_parse(
        file: UploadFile = File(...),
        background: bool = True,
        background_tasks: BackgroundTasks = None,
        user_id: str | None = Form(None),
        Tags: str | None = Form(None),
    ):
        """Upload a PDF and parse it.

        If background=True the task will be scheduled and a 202 returned
        with a "task_id". Otherwise the parsing will be done synchronously
        and the parsed document returned.
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
                    # run parser
                    doc = parser.parse(str(dest))
                    # attach optional metadata if provided
                    try:
                        if user_id:
                            doc.user_id = user_id
                        if Tags:
                            try:
                                doc.tags = json.loads(Tags)
                            except Exception:
                                # fallback: ignore malformed tags
                                pass
                    except Exception:
                        pass

                    # persistence should be implemented here (DB save)
                    print(f"Background parse finished: {task_id} (user_id={getattr(doc, 'user_id', None)})")
                except Exception as e:
                    print(f"Background parse failed: {e}")

            if background_tasks is None:
                raise HTTPException(
                    status_code=500,
                    detail="Background tasks unavailable",
                )

            background_tasks.add_task(_bg)
            return JSONResponse(status_code=202, content={"task_id": task_id})
        else:
            # Synchronous parsing path. Wrap in try/except to return
            # helpful traceback during local development.
            try:
                doc = parser.parse(str(dest))

                # attach optional metadata coming from the form
                if user_id:
                    try:
                        doc.user_id = user_id
                    except Exception:
                        pass

                if Tags:
                    try:
                        parsed_tags = json.loads(Tags)
                        if isinstance(parsed_tags, dict):
                            doc.tags = parsed_tags
                    except Exception:
                        # ignore malformed tags
                        pass

                text_summary = display_parsing_results(doc)
                parsed = (
                    doc.model_dump()
                    if hasattr(doc, "model_dump")
                    else getattr(doc, "dict", lambda: {})()
                )

                # Ensure all values (e.g. datetimes) are JSON-serializable
                return JSONResponse(
                    status_code=200,
                    content={"parsed": jsonable_encoder(parsed), "summary": text_summary},
                )
            except Exception as e:
                # Development helper: include traceback in response body so the
                # frontend / curl can show the error without opening server logs.
                import traceback as _tb

                tb = _tb.format_exc()
                # Log to server console as well
                print("Synchronous parse failed:", str(e))
                print(tb)
                return JSONResponse(
                    status_code=500,
                    content={"error": str(e), "traceback": tb},
                )
else:
    @router.post("/upload")
    async def upload_and_parse():
        # multipart not available in this environment (tests may run in a
        # minimal container). Return 501 to indicate the feature is missing.
        raise HTTPException(status_code=501, detail="multipart support not available")
