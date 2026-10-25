"""ASGI entry point.

Local development:  uvicorn main:app --reload
Production:         gunicorn -k uvicorn.workers.UvicornWorker main:app
"""

from backend.app.main import app

__all__ = ["app"]
