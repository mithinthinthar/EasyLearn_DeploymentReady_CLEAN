"""Vercel/Flask entrypoint for the deployment-safe History backend."""
from history_app_local import app

__all__ = ["app"]
