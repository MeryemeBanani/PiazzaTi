from fastapi import FastAPI, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from dotenv import load_dotenv
import os

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


# Carica le variabili dal file .env
load_dotenv()

# Setup OpenTelemetry con Resource configurato
resource = Resource.create({
    ResourceAttributes.SERVICE_NAME: "piazzati-backend",
    ResourceAttributes.SERVICE_VERSION: "1.0.0",
})

prometheus_reader = PrometheusMetricReader(
    disable_target_info=True  # Disabilita target_info che causa problemi di parsing
)
meter_provider = MeterProvider(
    metric_readers=[prometheus_reader],
    resource=resource
)
metrics.set_meter_provider(meter_provider)  # imposto il provider globale

tracer_provider = TracerProvider()  # tracce: richieste propagate nell'app
trace.set_tracer_provider(tracer_provider)  # imposto il provider globale


# Get meter and tracer dal modulo corrente "__name__"
meter = metrics.get_meter(__name__)
tracer = trace.get_tracer(__name__)

app = FastAPI(title="PiazzaTi Backend", version="1.0.0")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Instrument FastAPI automatically (per tracciare le richieste)
FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument()
Psycopg2Instrumentor().instrument()

# metriche personalizzate:
request_count = meter.create_counter(
    "piazzati_custom_requests_total",
    description="Total number of requests tracked by custom counter",
    unit="1"
)

request_duration = meter.create_histogram(
    "piazzati_custom_request_duration_seconds",
    description="Request duration in seconds tracked by custom histogram",
    unit="s"
)

database_operations = meter.create_counter(
    "piazzati_custom_database_operations_total",
    description="Total number of database operations tracked by custom counter",
    unit="1"
)

active_users = meter.create_up_down_counter(
    "piazzati_custom_active_users",
    description="Number of active users tracked by custom counter",
    unit="1"
)

# Creazione endpoint e gestione metriche


@app.get("/")
async def root(request: Request):
    accept = request.headers.get("accept", "")
    if "application/json" in accept:
        return {"message": "Sito in costruzione", "image": "/static/PIAZZATI.IT.png"}
    return HTMLResponse(
        """
        <html>
            <head><title>Sito in costruzione</title></head>
            <body style='text-align:center;'>
                <h1>Sito in costruzione</h1>
                <img src='/static/PIAZZATI.IT.png'
                     alt='Sito in costruzione'
                     style='max-width:400px;'>
            </body>
        </html>
        """
    )


@app.get("/metrics")
async def get_metrics():
    """Endpoint per le metriche Prometheus"""
    from fastapi import Response
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
async def health_check():
    """Endpoint per verificare lo stato dell'applicazione"""
    request_count.add(1, {"endpoint": "/health", "method": "GET"})
    database_url = os.getenv("DATABASE_URL")
    return {
        "status": "healthy",
        "database_configured": bool(database_url),
        "database_url_preview": (database_url[:30] + "..." if database_url else None)
    }


@app.get("/db-test")
async def test_database_connection(db: Session = Depends(get_db)):
    """Endpoint per testare la connessione al database"""
    request_count.add(1, {"endpoint": "/db-test", "method": "GET"})
    try:
        # Esegui una query semplice per testare la connessione
        database_operations.add(1, {"operation": "test_query"})
        db.execute(text("SELECT 1"))
        return {"status": "database_connected", "result": "OK"}
    except Exception as e:
        database_operations.add(1, {"operation": "test_query_error"})
        return {"status": "database_error", "error": str(e)}
