# Dockerfile per FastAPI backend
FROM python:3.11-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia i requisiti e installa le dipendenze
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copia il resto del codice
COPY . .

# Comando di avvio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
