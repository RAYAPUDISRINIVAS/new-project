"""Train and evaluate a screening model using the UCI Cleveland dataset."""

from __future__ import annotations

import argparse
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.schema import (
    CATEGORICAL_COLUMNS,
    CATEGORY_VALUES,
    FEATURE_COLUMNS,
    NUMERIC_BOUNDS,
    NUMERIC_COLUMNS,
    TARGET_COLUMN,
)

RAW_COLUMNS = FEATURE_COLUMNS + [TARGET_COLUMN]


def load_dataset(path: Path) -> tuple[pd.DataFrame, dict[str, int]]:
    """Read either canonical CSV or the original 14-column UCI data file."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Dataset not found at {path}. See data/README.md for the official source."
        )
    frame = pd.read_csv(path, na_values=["?", " NA", ""])
    if len(frame.columns) == len(RAW_COLUMNS) and list(frame.columns) != RAW_COLUMNS:
        frame = pd.read_csv(path, header=None, names=RAW_COLUMNS, na_values=["?", " NA", ""])
    frame.columns = [str(column).strip().lower() for column in frame.columns]
    if len(frame.columns) != len(RAW_COLUMNS) or set(frame.columns) != set(RAW_COLUMNS):
        raise ValueError(
            f"Dataset must contain exactly these columns: {', '.join(RAW_COLUMNS)}"
        )
    frame = frame[RAW_COLUMNS].apply(pd.to_numeric, errors="coerce")
    dropped_missing = int(frame.isna().any(axis=1).sum())
    frame = frame.dropna().copy()
    if frame.empty:
        raise ValueError("No complete numeric rows remain after removing missing values.")

    target_values = set(frame[TARGET_COLUMN].astype(int).unique())
    if not target_values.issubset({0, 1, 2, 3, 4}):
        raise ValueError("Target values must be UCI Cleveland labels 0, 1, 2, 3, or 4.")
    if not np.all(np.equal(frame[TARGET_COLUMN], frame[TARGET_COLUMN].astype(int))):
        raise ValueError("Target labels must be whole numbers.")
    for column, allowed in CATEGORY_VALUES.items():
        values = set(frame[column].astype(int).unique())
        if not values.issubset(allowed):
            raise ValueError(f"Unexpected category value in {column}: {sorted(values - allowed)}")
        if not np.all(np.equal(frame[column], frame[column].astype(int))):
            raise ValueError(f"Category column {column} must contain whole numbers.")
    for column, (minimum, maximum) in NUMERIC_BOUNDS.items():
        if not frame[column].between(minimum, maximum).all():
            raise ValueError(f"Values in {column} must be between {minimum} and {maximum}.")

    frame[TARGET_COLUMN] = (frame[TARGET_COLUMN] > 0).astype(int)
    if set(frame[TARGET_COLUMN].unique()) != {0, 1}:
        raise ValueError("The cleaned dataset must include both target classes.")
    return frame, {"rows_dropped_for_missing_values": dropped_missing}


def build_pipeline(classifier) -> Pipeline:
    """Construct preprocessing and estimator together to prevent data leakage."""
    numeric = Pipeline(
        [("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]
    )
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocess = ColumnTransformer(
        [
            ("numeric", numeric, NUMERIC_COLUMNS),
            ("categorical", categorical, CATEGORICAL_COLUMNS),
        ]
    )
    return Pipeline([("preprocess", preprocess), ("classifier", classifier)])


def train(data_path: Path, model_path: Path, evaluation_path: Path) -> dict:
    """Compare candidate pipelines by training-set cross-validation recall."""
    data, cleaning = load_dataset(data_path)
    X = data[FEATURE_COLUMNS]
    y = data[TARGET_COLUMN]
    if int(y.value_counts().min()) < 5:
        raise ValueError("At least five examples of each class are needed for 5-fold CV.")
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )
    candidates = {
        "Logistic Regression": LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=42
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=300, class_weight="balanced", random_state=42, n_jobs=-1
        ),
        "Gradient Boosting": GradientBoostingClassifier(random_state=42),
    }

    comparison = {}
    fitted_candidates = {}
    for name, classifier in candidates.items():
        pipeline = build_pipeline(classifier)
        scores = cross_val_score(
            pipeline, X_train, y_train, cv=5, scoring="recall", n_jobs=None
        )
        comparison[name] = {
            "selection_metric": "recall",
            "fold_scores": [float(score) for score in scores],
            "mean_recall": float(scores.mean()),
            "std_recall": float(scores.std()),
        }
        fitted_candidates[name] = pipeline

    selected_name = max(comparison, key=lambda name: comparison[name]["mean_recall"])
    selected_model = fitted_candidates[selected_name]
    selected_model.fit(X_train, y_train)
    predictions = selected_model.predict(X_test)
    try:
        probabilities = selected_model.predict_proba(X_test)[:, 1]
        auc = float(roc_auc_score(y_test, probabilities))
    except (AttributeError, IndexError, ValueError):
        auc = None

    metrics = {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision": float(precision_score(y_test, predictions, zero_division=0)),
        "recall": float(recall_score(y_test, predictions, zero_division=0)),
        "f1": float(f1_score(y_test, predictions, zero_division=0)),
        "roc_auc": auc,
        "confusion_matrix": confusion_matrix(y_test, predictions, labels=[0, 1]).tolist(),
    }
    report = {
        "dataset": "UCI Cleveland Heart Disease (processed)",
        "positive_label": "target > 0 (presence of disease in source dataset)",
        "selection_metric": "5-fold cross-validation recall on training split",
        "selected_model": selected_name,
        "comparison": comparison,
        "test_metrics": metrics,
        "test_size": int(len(y_test)),
        "training_size": int(len(y_train)),
        "cleaning": cleaning,
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "probabilities_exposed_to_users": False,
    }
    model_path.parent.mkdir(parents=True, exist_ok=True)
    evaluation_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(selected_model, model_path)
    evaluation_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    metadata = {
        "dataset": report["dataset"],
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "selected_model": selected_name,
        "training_size": report["training_size"],
        "test_size": report["test_size"],
        "trained_at_utc": report["evaluated_at_utc"],
        "python_version": platform.python_version(),
        "scikit_learn_version": sklearn.__version__,
    }
    model_path.with_name("metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/heart.csv"))
    parser.add_argument("--model", type=Path, default=Path("models/heart_model.joblib"))
    parser.add_argument("--evaluation", type=Path, default=Path("models/evaluation.json"))
    args = parser.parse_args()
    report = train(args.data, args.model, args.evaluation)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
