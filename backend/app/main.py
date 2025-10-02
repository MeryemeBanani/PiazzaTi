from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import get_db, engine
from dotenv import load_dotenv
import os

# Carica le variabili dal file .env
load_dotenv()

app = FastAPI(title="PiazzaTi Backend", version="1.0.0")

# Route di test per verificare la connessione al database
@app.get("/")
async def root():
    return {"message": "PiazzaTi Backend API"}

@app.get("/health")
async def health_check():
    """Endpoint per verificare lo stato dell'applicazione"""
    database_url = os.getenv("DATABASE_URL")
    return {
        "status": "healthy",
        "database_configured": bool(database_url),
        "database_url_preview": database_url[:30] + "..." if database_url else None
    }

@app.get("/db-test")
async def test_database_connection(db: Session = Depends(get_db)):
    """Endpoint per testare la connessione al database"""
    try:
        # Esegui una query semplice per testare la connessione
        result = db.execute("SELECT 1")
        return {"status": "database_connected", "result": "OK"}
    except Exception as e:
        return {"status": "database_error", "error": str(e)}

