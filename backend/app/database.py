import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Le variabili d'ambiente sono caricate da Docker Compose tramite env_file


# ottengo l'URL del database dal .env
DATABASE_URL = os.getenv("DATABASE_URL")

# If DATABASE_URL is not provided (e.g. in local tests), fall back to an
# in-memory SQLite database to allow the test-suite to run without a .env.
if not DATABASE_URL:
    # Note: using SQLite in-memory for tests and local runs. In production the
    # real DATABASE_URL should be provided via environment or Docker Compose.
    DATABASE_URL = "sqlite:///:memory:"
    print("[WARN] DATABASE_URL not found, defaulting to in-memory SQLite for tests")


# create the SQLAlchemy engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
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
