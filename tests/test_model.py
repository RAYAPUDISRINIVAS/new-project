import pytest

from ml.predict import ModelUnavailableError, load_model, make_prediction
from ml.schema import FEATURE_COLUMNS


class ConstantModel:
    def predict(self, frame):
        assert list(frame.columns) == FEATURE_COLUMNS
        return [1]


def valid_features():
    return {
        "age": 55, "sex": 1, "cp": 2, "trestbps": 130, "chol": 240, "fbs": 0,
        "restecg": 0, "thalach": 150, "exang": 0, "oldpeak": 1.2, "slope": 2,
        "ca": 0, "thal": 3,
    }


def test_prediction_uses_all_schema_fields():
    assert make_prediction(ConstantModel(), valid_features()) == {"prediction": 1}


def test_prediction_rejects_mismatched_schema():
    features = valid_features()
    del features["age"]
    with pytest.raises(ValueError, match="feature schema"):
        make_prediction(ConstantModel(), features)


def test_missing_model_has_clear_error(tmp_path):
    with pytest.raises(ModelUnavailableError, match="not found"):
        load_model(tmp_path / "missing.joblib")
