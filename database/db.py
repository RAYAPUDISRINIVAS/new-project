"""SQLite connection and history operations."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import current_app, g


def get_db() -> sqlite3.Connection:
    """Return one SQLite connection per request context."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_error=None) -> None:
    """Close the current request's connection, if one was opened."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app) -> None:
    """Register connection cleanup and create the history table."""
    app.teardown_appcontext(close_db)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    with app.app_context():
        db = get_db()
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                features_json TEXT NOT NULL,
                prediction INTEGER NOT NULL CHECK (prediction IN (0, 1))
            )
            """
        )
        db.commit()


def save_prediction(db: sqlite3.Connection, features: dict, prediction: int) -> int:
    """Persist a validated prediction without storing identifying information."""
    cursor = db.execute(
        "INSERT INTO predictions (created_at, features_json, prediction) VALUES (?, ?, ?)",
        (
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
            json.dumps(features, sort_keys=True),
            int(prediction),
        ),
    )
    db.commit()
    return int(cursor.lastrowid)


def list_predictions(
    db: sqlite3.Connection, page: int = 1, per_page: int = 10, search: str = ""
) -> tuple[list[dict], int]:
    """Return a paginated, parameterized search over saved feature values/results."""
    page = max(page, 1)
    per_page = min(max(per_page, 1), 100)
    clauses = ""
    params: list = []
    if search:
        clauses = "WHERE features_json LIKE ? OR CAST(prediction AS TEXT) LIKE ? OR created_at LIKE ?"
        needle = f"%{search}%"
        params.extend([needle, needle, needle])
    total = db.execute(
        f"SELECT COUNT(*) FROM predictions {clauses}", params
    ).fetchone()[0]
    rows = db.execute(
        f"""
        SELECT id, created_at, features_json, prediction
        FROM predictions {clauses}
        ORDER BY id DESC
        LIMIT ? OFFSET ?
        """,
        [*params, per_page, (page - 1) * per_page],
    ).fetchall()
    return [
        {
            "id": row["id"],
            "created_at": row["created_at"],
            "features": json.loads(row["features_json"]),
            "prediction": row["prediction"],
        }
        for row in rows
    ], total
