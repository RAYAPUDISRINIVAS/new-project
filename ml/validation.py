"""Validated form fields for supported model inputs."""

from flask_wtf import FlaskForm
from wtforms import FloatField, IntegerField, SelectField
from wtforms.validators import InputRequired, NumberRange


class PatientForm(FlaskForm):
    """Collect only values supported by the documented model schema."""

    age = IntegerField("Age (years)", validators=[InputRequired(), NumberRange(18, 100)])
    sex = SelectField(
        "Sex (dataset category)", choices=[("0", "Female (0)"), ("1", "Male (1)")],
        coerce=int, validators=[InputRequired()],
    )
    cp = SelectField(
        "Chest pain type",
        choices=[
            ("1", "Typical angina"),
            ("2", "Atypical angina"),
            ("3", "Non-anginal pain"),
            ("4", "Asymptomatic"),
        ],
        coerce=int,
        validators=[InputRequired()],
    )
    trestbps = IntegerField(
        "Resting blood pressure (mm Hg)",
        validators=[InputRequired(), NumberRange(60, 250)],
    )
    chol = IntegerField(
        "Serum cholesterol (mg/dL)", validators=[InputRequired(), NumberRange(80, 700)]
    )
    fbs = SelectField(
        "Fasting blood sugar > 120 mg/dL",
        choices=[("0", "No"), ("1", "Yes")],
        coerce=int,
        validators=[InputRequired()],
    )
    restecg = SelectField(
        "Resting ECG result",
        choices=[
            ("0", "Normal"),
            ("1", "ST-T wave abnormality"),
            ("2", "Left ventricular hypertrophy"),
        ],
        coerce=int,
        validators=[InputRequired()],
    )
    thalach = IntegerField(
        "Maximum heart rate achieved (bpm)",
        validators=[InputRequired(), NumberRange(40, 250)],
    )
    exang = SelectField(
        "Exercise-induced angina",
        choices=[("0", "No"), ("1", "Yes")],
        coerce=int,
        validators=[InputRequired()],
    )
    oldpeak = FloatField(
        "ST depression induced by exercise",
        validators=[InputRequired(), NumberRange(0, 10)],
    )
    slope = SelectField(
        "Slope of peak exercise ST segment",
        choices=[("1", "Upsloping"), ("2", "Flat"), ("3", "Downsloping")],
        coerce=int,
        validators=[InputRequired()],
    )
    ca = SelectField(
        "Major vessels colored by fluoroscopy (0–3)",
        choices=[(str(value), str(value)) for value in range(4)],
        coerce=int,
        validators=[InputRequired()],
    )
    thal = SelectField(
        "Thalassemia category",
        choices=[("3", "Normal"), ("6", "Fixed defect"), ("7", "Reversible defect")],
        coerce=int,
        validators=[InputRequired()],
    )

    def as_features(self) -> dict[str, int | float]:
        """Return validated values using the model's canonical column names."""
        names = (
            "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
            "thalach", "exang", "oldpeak", "slope", "ca", "thal",
        )
        return {name: getattr(self, name).data for name in names}
