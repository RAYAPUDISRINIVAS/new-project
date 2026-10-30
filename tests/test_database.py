import sqlite3

from database.db import list_predictions, save_prediction


def make_db():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute(
        """CREATE TABLE predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        features_json TEXT NOT NULL,
        prediction INTEGER NOT NULL CHECK (prediction IN (0, 1))
        )"""
    )
    return db


def test_save_and_paginate_predictions():
    db = make_db()
    features = {"age": 52, "chol": 210}
    first_id = save_prediction(db, features, 1)
    save_prediction(db, {"age": 60}, 0)

    records, total = list_predictions(db, page=1, per_page=1)

    assert first_id == 1
    assert total == 2
    assert len(records) == 1
    assert records[0]["prediction"] == 0


def test_history_search_is_parameterized_and_matches_feature_json():
    db = make_db()
    save_prediction(db, {"age": 52}, 1)

    records, total = list_predictions(db, search="52")
    malicious, malicious_total = list_predictions(db, search="' OR 1=1 --")

    assert total == 1
    assert records[0]["features"] == {"age": 52}
    assert malicious_total == 0
    assert malicious == []
