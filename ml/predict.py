"""Model loading and single-record prediction helpers."""

from pathlib import Path

import joblib
import pandas as pd

from ml.schema import FEATURE_COLUMNS


class ModelUnavailableError(RuntimeError):
    """Raised when no trained model is available for prediction."""


def load_model(path: str | Path):
    """Load a previously trained scikit-learn pipeline."""
    model_path = Path(path)
    if not model_path.is_file():
        raise ModelUnavailableError(f"Trained model not found: {model_path}")
    model = joblib.load(model_path)
    if not callable(getattr(model, "predict", None)):
        raise ModelUnavailableError("The saved artifact does not provide predict().")
    return model


def make_prediction(model, features: dict[str, int | float]) -> dict[str, int]:
    """Predict the binary dataset label without presenting probability as clinical risk."""
    if set(features) != set(FEATURE_COLUMNS):
        raise ValueError("Input fields do not match the model's required feature schema.")
    row = pd.DataFrame([{name: features[name] for name in FEATURE_COLUMNS}])
    prediction = int(model.predict(row)[0])
    if prediction not in (0, 1):
        raise ValueError("The model returned an unsupported target label.")
    return {"prediction": prediction}
