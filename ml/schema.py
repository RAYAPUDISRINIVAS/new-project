"""The feature schema for the UCI Cleveland Heart Disease dataset."""

FEATURE_COLUMNS = [
    "age",
    "sex",
    "cp",
    "trestbps",
    "chol",
    "fbs",
    "restecg",
    "thalach",
    "exang",
    "oldpeak",
    "slope",
    "ca",
    "thal",
]
TARGET_COLUMN = "target"

CATEGORICAL_COLUMNS = ["sex", "cp", "fbs", "restecg", "exang", "slope", "ca", "thal"]
NUMERIC_COLUMNS = ["age", "trestbps", "chol", "thalach", "oldpeak"]

CATEGORY_VALUES = {
    "sex": {0, 1},
    "cp": {1, 2, 3, 4},
    "fbs": {0, 1},
    "restecg": {0, 1, 2},
    "exang": {0, 1},
    "slope": {1, 2, 3},
    "ca": {0, 1, 2, 3},
    "thal": {3, 6, 7},
}

# Broad, documented application input bounds; these are not learned model ranges.
NUMERIC_BOUNDS = {
    "age": (18, 100),
    "trestbps": (60, 250),
    "chol": (80, 700),
    "thalach": (40, 250),
    "oldpeak": (0.0, 10.0),
}

FEATURE_LABELS = {
    "age": "Age (years)",
    "sex": "Sex (dataset category)",
    "cp": "Chest pain type",
    "trestbps": "Resting blood pressure (mm Hg)",
    "chol": "Serum cholesterol (mg/dL)",
    "fbs": "Fasting blood sugar > 120 mg/dL",
    "restecg": "Resting ECG result",
    "thalach": "Maximum heart rate achieved (bpm)",
    "exang": "Exercise-induced angina",
    "oldpeak": "ST depression induced by exercise",
    "slope": "Slope of peak exercise ST segment",
    "ca": "Major vessels colored by fluoroscopy (0–3)",
    "thal": "Thalassemia category",
}
