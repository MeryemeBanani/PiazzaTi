# Multi-stage Dockerfile per FastAPI backend - Produzione ottimizzata
FROM python:3.13-slim as builder

# Installa dipendenze di sistema per build
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Crea virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copia e installa requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Stage finale - immagine più leggera
FROM python:3.13-slim

# Crea utente non-root per sicurezza
RUN groupadd -r piazzati && useradd -r -g piazzati piazzati

# Copia virtual environment dal builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Imposta directory di lavoro
WORKDIR /app

# Copia codice applicazione
COPY --chown=piazzati:piazzati . .

# Cambia a utente non-root
USER piazzati

# Esponi porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Comando di avvio ottimizzato per produzione
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--access-log"]
