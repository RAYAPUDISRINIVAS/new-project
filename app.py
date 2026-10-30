"""Flask application for the educational cardiovascular screening demo."""

from __future__ import annotations

import logging
from pathlib import Path

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFProtect

from config import Config
from database.db import get_db, init_app as init_database, list_predictions, save_prediction
from ml.predict import ModelUnavailableError, load_model, make_prediction
from ml.validation import PatientForm


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    CSRFProtect(app)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    init_database(app)

    try:
        app.extensions["prediction_model"] = load_model(app.config["MODEL_PATH"])
    except ModelUnavailableError:
        app.extensions["prediction_model"] = None
        app.logger.warning(
            "Prediction model is unavailable. Run ml/train_model.py after adding the dataset."
        )
    except Exception:
        app.extensions["prediction_model"] = None
        app.logger.exception("The prediction model could not be loaded.")

    @app.context_processor
    def inject_history_setting():
        return {"history_enabled": app.config["STORE_PREDICTIONS"]}

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            model_available=app.extensions["prediction_model"] is not None,
        )

    @app.route("/predict", methods=["GET", "POST"])
    def predict():
        form = PatientForm()
        if form.validate_on_submit():
            model = app.extensions["prediction_model"]
            if model is None:
                flash(
                    "The trained model is not available yet. Follow the dataset and training "
                    "steps in the README, then restart the app.",
                    "error",
                )
                return render_template("predict.html", form=form), 503
            try:
                features = form.as_features()
                result = make_prediction(model, features)
                prediction_id = None
                if app.config["STORE_PREDICTIONS"]:
                    prediction_id = save_prediction(
                        get_db(), features, result["prediction"]
                    )
            except ValueError as exc:
                form.form_error = str(exc)
                return render_template("predict.html", form=form), 400
            return render_template(
                "result.html",
                prediction_id=prediction_id,
                features=features,
                prediction=result["prediction"],
            )
        return render_template("predict.html", form=form), (400 if request.method == "POST" else 200)

    @app.get("/history")
    def history():
        if not app.config["STORE_PREDICTIONS"]:
            abort(404)
        page = request.args.get("page", default=1, type=int)
        search = request.args.get("q", default="", type=str).strip()[:100]
        page = max(page or 1, 1)
        records, total = list_predictions(get_db(), page=page, per_page=10, search=search)
        return render_template(
            "history.html",
            records=records,
            total=total,
            page=page,
            pages=max(1, (total + 9) // 10),
            search=search,
        )

    @app.post("/history/clear")
    def clear_history():
        if not app.config["STORE_PREDICTIONS"]:
            abort(404)
        if request.form.get("confirm_clear") != "yes":
            flash("Confirm the action before clearing prediction history.", "error")
            return redirect(url_for("history"))
        get_db().execute("DELETE FROM predictions")
        get_db().commit()
        flash("Prediction history was cleared from this demonstration app.", "success")
        return redirect(url_for("history"))

    @app.get("/model-performance")
    def model_performance():
        report_path = Path(app.config["EVALUATION_PATH"])
        report = None
        if report_path.is_file():
            import json

            try:
                report = json.loads(report_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                app.logger.exception("Could not read the saved model evaluation report.")
                flash("The saved evaluation report could not be read.", "error")
        return render_template("performance.html", report=report)

    @app.get("/health")
    def health():
        model_loaded = app.extensions["prediction_model"] is not None
        return jsonify(
            status="ok" if model_loaded else "degraded",
            prediction_model="loaded" if model_loaded else "unavailable",
        ), (200 if model_loaded else 503)

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(_error):
        logging.getLogger(__name__).exception("Unhandled application error.")
        return render_template("500.html"), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=False)
