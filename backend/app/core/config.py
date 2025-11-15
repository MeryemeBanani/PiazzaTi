import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://piazzati_user:piazzati_password@localhost:5432/db_piazzati")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    WORKER_TIMEOUT: int = int(os.getenv("WORKER_TIMEOUT", 300))
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", 4))
    # Aggiungi qui altre variabili d'ambiente se servono

settings = Settings()
