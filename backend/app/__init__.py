"""
Package initializer for backend.app

This file makes `backend/app` a proper Python package so imports like
`from app.parsers.ollama_cv_parser import ...` work when running scripts
from the `backend` directory or the repo root.

No runtime logic here — kept minimal on purpose.
"""

__all__ = [
    "parsers",
    "schemas",
    "api",
    "models",
    "core",
    "utils",
    "static",
]
