from fastapi import FastAPI
from fastapi import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import Counter, Histogram
import time

# Create Prometheus metrics
REQUEST_COUNT = Counter('piazzati_requests_total', 'Total number of requests', ['endpoint', 'method'])
REQUEST_DURATION = Histogram('piazzati_request_duration_seconds', 'Request duration in seconds')

app = FastAPI(title="PiazzaTi Backend", version="1.0.0")

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(endpoint=request.url.path, method=request.method).inc()
    REQUEST_DURATION.observe(duration)
    
    return response

@app.get("/")
async def root():
    return {"message": "PiazzaTi Backend API with Monitoring"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "monitoring": "enabled"}

@app.get("/metrics")
async def get_metrics():
    """Endpoint per le metriche Prometheus"""
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)