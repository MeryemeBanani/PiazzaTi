from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import os
import uuid
import json

INPUT_FOLDER = "/var/lib/docker/piazzati-data/jds"

router = APIRouter()

@router.post("/jd/upload")
async def upload_jd(request: Request):
    jd_data = await request.json()
    os.makedirs(INPUT_FOLDER, exist_ok=True)
    filename = f"jd_{uuid.uuid4().hex}.json"
    filepath = os.path.join(INPUT_FOLDER, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(jd_data, f, ensure_ascii=False, indent=2)
    return JSONResponse({"status": "ok", "filename": filename})
