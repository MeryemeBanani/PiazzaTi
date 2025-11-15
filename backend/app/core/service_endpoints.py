import os
from fastapi import APIRouter, Response, Depends
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..database import get_db
from .metrics import request_count, database_operations
from .config import settings

router = APIRouter()

@router.get("/metrics")
async def get_metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

@router.get("/health")
async def health_check():
    request_count.add(1, {"endpoint": "/health", "method": "GET"})
    database_url = settings.DATABASE_URL
    return {
        "status": "healthy",
        "database_configured": bool(database_url),
        "database_url_preview": (database_url[:30] + "..." if database_url else None),
    }

@router.get("/db-test")
async def test_database_connection(db: Session = Depends(get_db)):
    request_count.add(1, {"endpoint": "/db-test", "method": "GET"})
    try:
        database_operations.add(1, {"operation": "test_query"})
        db.execute(text("SELECT 1"))
        return {"status": "database_connected", "result": "OK"}
    except Exception as e:
        database_operations.add(1, {"operation": "test_query_error"})
        return {"status": "database_error", "error": str(e)}
