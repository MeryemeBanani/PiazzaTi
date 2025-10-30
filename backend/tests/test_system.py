#!/usr/bin/env python3
"""
Test completo del sistema PiazzaTi
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests  # noqa: E402
from app.database import engine  # noqa: E402
from sqlalchemy import text  # noqa: E402


def test_database():
    print("Test Database PostgreSQL + pgvector...")

    try:
        with engine.connect() as conn:
            # Test connessione
            print("OK - Connessione database: OK")

            # Test PostgreSQL version e stato
            result = conn.execute(text("SELECT version()"))
            pg_version = result.fetchone()[0]
            print(f"OK - PostgreSQL: {pg_version.split(',')[0]}")

            # Test che PostgreSQL accetti scritture
            result = conn.execute(text("SELECT pg_is_in_recovery()"))
            is_readonly = result.fetchone()[0]
            print(
                f"OK - Database stato: {'READ-ONLY' if is_readonly else 'READ-WRITE'}"
            )

            # Count tabelle
            result = conn.execute(
                text("SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public'")
            )
            table_count = result.fetchone()[0]
            print(f"OK - Tabelle create: {table_count}")

            # Lista tabelle
            result = conn.execute(
                text(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
                )
            )
            tables = [row[0] for row in result]
            print(f"INFO - Tabelle: {', '.join(tables)}")

            # Test pgvector
            result = conn.execute(
                text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            )
            ext = result.fetchone()
            print(f"OK - pgvector: {'INSTALLATO' if ext else 'MANCANTE'}")

            # Test vincoli
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.check_constraints WHERE constraint_schema = 'public'"
                )
            )
            constraints = result.fetchone()[0]
            print(f"OK - Check constraints: {constraints}")

            # Test indici
            result = conn.execute(
                text("SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public'")
            )
            indexes = result.fetchone()[0]
            print(f"OK - Indici creati: {indexes}")

            # Test pratico: inserimento e lettura di un record di test
            conn.execute(text("CREATE TEMP TABLE test_table (id SERIAL, name TEXT)"))
            conn.execute(text("INSERT INTO test_table (name) VALUES ('test_piazzati')"))
            result = conn.execute(text("SELECT name FROM test_table WHERE id = 1"))
            test_data = result.fetchone()[0]
            if test_data == "test_piazzati":
                print("OK - Test scrittura/lettura: OK")
            else:
                print("ERROR - Test scrittura/lettura: FALLITO")
            conn.commit()

    except Exception as e:
        print(f"ERROR - Errore database: {e}")


def test_backend():
    print("\nTest Backend FastAPI...")

    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("OK - Backend FastAPI: ONLINE")
        else:
            print(f"WARN - Backend risponde con status: {response.status_code}")
    except Exception as e:
        print(f"ERROR - Backend non raggiungibile: {e}")


def test_monitoring():
    print("\nTest Sistema Monitoraggio...")

    # Test Prometheus
    try:
        response = requests.get("http://localhost:9090/-/healthy", timeout=5)
        if response.status_code == 200:
            print("OK - Prometheus: ONLINE")
        else:
            print(f"WARN - Prometheus status: {response.status_code}")
    except Exception as e:
        print(f"ERROR - Prometheus non raggiungibile: {e}")

    # Test Grafana (homepage)
    try:
        response = requests.get("http://localhost:3000/login", timeout=5)
        if response.status_code == 200:
            print("OK - Grafana: ONLINE")
        else:
            print(f"WARN - Grafana status: {response.status_code}")
    except Exception as e:
        print(f"ERROR - Grafana non raggiungibile: {e}")

    # Test che le metriche vengano esposte correttamente
    try:
        response = requests.get("http://localhost:8000/metrics", timeout=5)
        if response.status_code == 200 and "piazzati_custom" in response.text:
            print("OK - Metriche FastAPI: ESPOSTE")
        else:
            print(f"WARN - Metriche FastAPI: {response.status_code}")
    except Exception as e:
        print(f"ERROR - Endpoint metriche non raggiungibile: {e}")


if __name__ == "__main__":
    print("TEST SISTEMA PIAZZATI COMPLETO\n")

    test_database()
    test_backend()
    test_monitoring()

    print("\nTest completato!")
