#!/usr/bin/env python3
"""
Test script for monitoring functionality
"""
import pytest
from fastapi.testclient import TestClient
import os
from unittest.mock import patch

# Mock environment variables per evitare errori database
@patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost:5432/test_db"})
def get_test_app():
    """Importa l'app con environment mockato"""
    from app.main import app
    return app

def test_health_endpoint():
    """Test dell'endpoint /health"""
    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost:5432/test_db"}):
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

@pytest.mark.parametrize(
    "accept,expected_type",
    [("application/json", dict), ("text/html", str)],
)
def test_root_endpoint_variants(accept, expected_type):
    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost:5432/test_db"}):
        from app.main import app
        client = TestClient(app)
        response = client.get("/", headers={"accept": accept})
        assert response.status_code == 200
        if expected_type is dict:
            assert response.json()["message"] == "Benvenuto su PiazzaTi!"
        else:
            assert "<html>" in response.text

def test_metrics_endpoint():
    """Test dell'endpoint /metrics"""
    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost:5432/test_db"}):
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/metrics")
        assert response.status_code == 200
        
        # Verifica content-type Prometheus
        content_type = response.headers.get("content-type")
        assert "text/plain" in content_type
        
        # Verifica presenza metriche chiave
        metrics_text = response.text
        assert "piazzati_custom_requests_1_total" in metrics_text  # Le nostre metriche custom
        assert "http_server" in metrics_text  # Metriche automatiche OpenTelemetry
        assert "python_gc" in metrics_text  # Metriche Python standard

def test_multiple_requests_generate_metrics():
    """Test che più richieste generino metriche incrementali"""
    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost:5432/test_db"}):
        from app.main import app
        client = TestClient(app)
        
        # Prima richiesta
        response1 = client.get("/health")
        assert response1.status_code == 200
        
        # Seconda richiesta  
        response2 = client.get("/health")
        assert response2.status_code == 200
        
        # Verifica metriche
        metrics_response = client.get("/metrics")
        assert metrics_response.status_code == 200
        
        metrics_text = metrics_response.text
        # Dovrebbero esserci almeno le richieste che abbiamo fatto
        assert "piazzati_requests" in metrics_text