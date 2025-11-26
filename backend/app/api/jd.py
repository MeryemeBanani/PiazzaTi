from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import os
import uuid
import json

INPUT_FOLDER = "/app/NLP/data/jds"

router = APIRouter()

@router.post("/jd/upload")
async def upload_jd(request: Request):
    import sys
    try:
        jd_data = await request.json()
        print("[JD UPLOAD] Ricevuta richiesta:", jd_data, file=sys.stderr)
        filename = f"jd_{uuid.uuid4().hex}.json"
        filepath = os.path.join(INPUT_FOLDER, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(jd_data, f, ensure_ascii=False, indent=2)
        print(f"[JD UPLOAD] File salvato: {filepath}", file=sys.stderr)
        # Ora la generazione embedding JD e il matching sono gestiti solo dal batch processor.
        return JSONResponse({"status": "ok", "filename": filename})
    except PermissionError as e:
        print(f"[JD UPLOAD] PermissionError: {e}", file=sys.stderr)
        return JSONResponse({"status": "error", "detail": "Permission denied", "message": str(e)}, status_code=500)
    except Exception as e:
        print(f"[JD UPLOAD] Unexpected error: {e}", file=sys.stderr)
        return JSONResponse({"status": "error", "detail": "Unexpected error", "message": str(e)}, status_code=500)
