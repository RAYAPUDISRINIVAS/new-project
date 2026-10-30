import pytest

from app import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-key",
            "DATABASE": str(tmp_path / "test.sqlite3"),
            "MODEL_PATH": str(tmp_path / "missing.joblib"),
            "EVALUATION_PATH": str(tmp_path / "missing.json"),
        }
    )
    app.extensions["prediction_model"] = None
    return app.test_client()


def test_dashboard_and_health_without_model(client):
    assert client.get("/").status_code == 200
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json["prediction_model"] == "unavailable"


def test_prediction_form_rejects_out_of_range_value(client):
    response = client.post("/predict", data={"age": "150"})
    assert response.status_code == 400
    assert b"Age" in response.data


def test_prediction_form_rejects_unsupported_category(client):
    response = client.post("/predict", data={"cp": "99"})
    assert response.status_code == 400
    assert b"Chest pain type" in response.data


def test_missing_model_is_reported_without_fake_prediction(client):
    response = client.post(
        "/predict",
        data={
            "age": 55, "sex": 1, "cp": 2, "trestbps": 130, "chol": 240, "fbs": 0,
            "restecg": 0, "thalach": 150, "exang": 0, "oldpeak": 1.2, "slope": 2,
            "ca": 0, "thal": 3,
        },
    )
    assert response.status_code == 503
    assert b"model is not available" in response.data
    assert client.get("/history").data.count(b"Prediction history is empty") == 1


def test_clear_history_requires_confirmation(client):
    response = client.post("/history/clear", data={"confirm_clear": "no"})
    assert response.status_code == 302
    assert client.get("/history").status_code == 200


def test_state_changing_routes_require_csrf(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "csrf-test-key",
            "DATABASE": str(tmp_path / "csrf.sqlite3"),
            "MODEL_PATH": str(tmp_path / "missing.joblib"),
            "EVALUATION_PATH": str(tmp_path / "missing.json"),
        }
    )
    response = app.test_client().post(
        "/history/clear", data={"confirm_clear": "yes"}
    )
    assert response.status_code == 400


def test_public_mode_does_not_store_or_expose_prediction_history(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-key",
            "STORE_PREDICTIONS": False,
            "DATABASE": str(tmp_path / "public.sqlite3"),
            "MODEL_PATH": str(tmp_path / "missing.joblib"),
            "EVALUATION_PATH": str(tmp_path / "missing.json"),
        }
    )

    class FixedModel:
        def predict(self, _features):
            return [0]

    app.extensions["prediction_model"] = FixedModel()
    client = app.test_client()
    response = client.post(
        "/predict",
        data={
            "age": 55, "sex": 1, "cp": 2, "trestbps": 130, "chol": 240, "fbs": 0,
            "restecg": 0, "thalach": 150, "exang": 0, "oldpeak": 1.2, "slope": 2,
            "ca": 0, "thal": 3,
        },
    )

    assert response.status_code == 200
    assert b"NOT SAVED" in response.data
    assert b"View saved history" not in response.data
    assert client.get("/history").status_code == 404
    assert client.post("/history/clear").status_code == 404

    import sqlite3

    with sqlite3.connect(app.config["DATABASE"]) as db:
        assert db.execute("SELECT COUNT(*) FROM predictions").fetchone()[0] == 0
