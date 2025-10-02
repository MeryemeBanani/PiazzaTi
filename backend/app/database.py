from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# carica il file .env
load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL") # ottengo l'URL del database dal .env

if not DATABASE_URL:
    raise ValueError("DATABASE_URL non trovata nel file .env")


engine = create_engine(DATABASE_URL) # creo il motore SQLAlchemy

# Crea la SessionLocal per le transazioni
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base per i modelli
Base = declarative_base()

# Dependency per ottenere la sessione del database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()