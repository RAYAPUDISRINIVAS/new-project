"""Environment-based configuration for the Flask application."""

import os
import secrets
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Default configuration; production secrets should come from the environment."""

    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DATABASE = os.environ.get(
        "DATABASE_PATH", str(BASE_DIR / "instance" / "predictions.sqlite3")
    )
    MODEL_PATH = os.environ.get("MODEL_PATH", str(BASE_DIR / "models" / "heart_model.joblib"))
    EVALUATION_PATH = os.environ.get(
        "EVALUATION_PATH", str(BASE_DIR / "models" / "evaluation.json")
    )
    STORE_PREDICTIONS = os.environ.get("STORE_PREDICTIONS", "true").lower() == "true"
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    MAX_CONTENT_LENGTH = 16 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"
