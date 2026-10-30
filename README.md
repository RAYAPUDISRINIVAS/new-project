# Cardiovascular Disease Prediction System

A beginner-friendly Flask and scikit-learn demonstration that trains a binary classifier on the **processed UCI Cleveland Heart Disease dataset**. It accepts the dataset's 13 documented inputs, saves an evaluation report and model pipeline, and optionally records non-identifying prediction inputs in local SQLite.

> **Educational use only.** This project is not clinically validated or intended for diagnosis, treatment, triage, or health decisions. Model classes are dataset labels, not confirmed clinical risk or a calibrated patient probability. Seek advice from a qualified healthcare professional.

## Architecture

```text
app.py ── Flask routes, startup model loading, CSRF, templates
├── config.py ── environment-based settings
├── ml/
│   ├── schema.py ── canonical feature names, domains and dataset categories
│   ├── validation.py ── bounded, allow-listed form fields
│   ├── train_model.py ── data checks, preprocessing, CV selection, held-out report
│   ├── predict.py ── pipeline loading and validated inference
│   └── evaluate_model.py ── print saved evaluation
├── database/db.py ── local SQLite prediction history
├── templates/ and static/ ── responsive Bootstrap UI and Chart.js visualizations
├── data/README.md ── official dataset source and file format
└── tests/ ── route, validation, model-loading and database tests
```

The training pipeline uses a stratified hold-out split before cross-validation/model fitting. Preprocessing (median/mode imputation, numeric scaling, categorical one-hot encoding) is inside each scikit-learn pipeline, so it is fit only on each training fold. Candidate models are compared using 5-fold recall on the training partition, chosen by that predefined screening-oriented metric, then evaluated once on the held-out test partition. No performance values are hardcoded.

## Requirements and dataset

- Python 3.10 or newer
- Dataset: [UCI Machine Learning Repository — Heart Disease](https://archive.ics.uci.edu/dataset/45/heart+disease), processed Cleveland subset
- Download `processed.cleveland.data` from the official UCI dataset page and save as `data/heart.csv`. Full file/schema and label mapping notes are in [data/README.md](data/README.md).

The UCI Cleveland source has exactly 13 input fields and target `num` (0–4); it does **not** contain glucose measurements. In this application `fbs` means the dataset's fasting blood sugar category (>120 mg/dL); it is not a glucose measurement. The script maps `num=0` to class 0 and `num=1..4` to class 1, and drops incomplete rows. The number dropped is included in evaluation output. It does not create synthetic clinical observations.

## Windows PowerShell setup and run

Run these commands from the project directory in the VS Code terminal. If starting elsewhere, first create and enter a folder:

```powershell
New-Item -ItemType Directory -Force cardiovascular-prediction
Set-Location cardiovascular-prediction
```

1. Create and activate a virtual environment:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation for this terminal, use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and activate again.

2. Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

3. Get the dataset. Visit the official dataset page linked above, download its data archive, extract it, then place the file named `processed.cleveland.data` at `data\heart.csv`. Alternatively, if using the UCI archive URL available at download time:

```powershell
Invoke-WebRequest -Uri "https://archive.ics.uci.edu/static/public/45/heart+disease.zip" -OutFile "$env:TEMP\uci-heart.zip"
Expand-Archive -Path "$env:TEMP\uci-heart.zip" -DestinationPath "$env:TEMP\uci-heart" -Force
Get-ChildItem "$env:TEMP\uci-heart" -Recurse -Filter "processed.cleveland.data"
Copy-Item (Get-ChildItem "$env:TEMP\uci-heart" -Recurse -Filter "processed.cleveland.data" | Select-Object -First 1).FullName "data\heart.csv"
```

The download URL/archive layout may change; the official dataset page and its instructions are authoritative. Check that `data\heart.csv` exists before training.

4. Train and evaluate the model:

```powershell
python -m ml.train_model
```

This creates `models\heart_model.joblib`, `models\evaluation.json`, and `models\metadata.json`. The evaluation JSON includes the real CV comparison, test metrics, confusion matrix, sample counts, and dropped-row count. For a concise readout later:

```powershell
python -m ml.evaluate_model
```

5. Run automated tests:

```powershell
python -m pytest -q
```

6. (Optional) Configure a non-default secret for local use, then run Flask:

```powershell
$env:SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). To stop the development server, press `Ctrl+C`.

The default app binds to loopback (`127.0.0.1`) with debug mode disabled. Do not expose Flask's development server to the public internet.

## Deploy to Render

The repository includes a Render Blueprint in `render.yaml`. The trained model and its real evaluation report are included so the deployed app can start without the source dataset. To deploy:

1. Push this project to a GitHub repository.
2. In Render, choose **New → Blueprint**, connect the repository, and apply the `render.yaml` configuration.
3. Wait for the first deployment, then open the service's `onrender.com` URL. The Blueprint generates a secret key and enables secure cookies.

The hosted demo sets `STORE_PREDICTIONS=false`: submitted measurements are used to produce the result but are not saved, and history endpoints are disabled. The default local setting remains enabled for the SQLite history demonstration. Do not enter real or identifiable health information into a public demo.

## How the files connect

`app.py` creates the Flask app, initializes SQLite, and attempts to load the trained pipeline once at startup. `ml/validation.py` defines the allowed form values; `ml/schema.py` is the canonical feature definition shared by inference and training. With local history enabled, a successful POST calls `ml/predict.py` and saves the measurements and binary output to `database/db.py`. Set `STORE_PREDICTIONS=false` to disable storage and history routes. CSRF protection applies to state-changing requests, including history deletion. `/model-performance` reads only the training script's saved report and never substitutes example values.

The prediction page returns a clear setup message (HTTP 503) when the model file does not exist. The app can still start and serve the dashboard, history, performance page, and health status. `/health` reports `degraded` and status 503 until the artifact is available. If there is no dataset, follow step 3 and train; prediction requires those genuine model artifacts and no fake output is used.

## Troubleshooting

- **Dataset not found:** verify the file is at `data\heart.csv`; inspect [data/README.md](data/README.md) for accepted raw and canonical formats.
- **Unexpected columns/categories:** use the original processed Cleveland file or the exact canonical CSV header. The trainer rejects unsupported category and numeric-domain values rather than guessing their meaning.
- **Missing model / health is degraded:** train successfully, confirm `models\heart_model.joblib` exists, then restart Flask so the startup loader can load it.
- **Evaluation report missing:** run `python -m ml.train_model`; the UI intentionally does not display placeholder metrics.
- **Port is occupied:** set `$env:PORT = "5001"` before `python app.py`, then visit `http://127.0.0.1:5001`.
- **CSRF failure:** reload the form to obtain a fresh token. Do not disable CSRF outside tests.
- **Stored history:** rows are local to the configured SQLite database; use the History page's clear action to remove records. The database is excluded from Git.

## Data and privacy notes

When local prediction history is enabled, it stores a UTC timestamp, the 13 submitted feature values, and the model's binary result. No names, telephone numbers, or contact details are requested. The hosted Render configuration disables prediction storage. This is an educational demonstration, not a production health-data service. Avoid entering identifiable or sensitive personal health information.
