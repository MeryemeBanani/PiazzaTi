import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Le variabili d'ambiente sono caricate da Docker Compose tramite env_file


# ottengo l'URL del database dal .env
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL non trovata nel file .env")


# creo il motore SQLAlchemy
engine = create_engine(DATABASE_URL)

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
