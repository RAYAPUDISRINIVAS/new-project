# Dataset setup

This project is structured for the **processed Cleveland subset** of the UCI Heart Disease dataset (303 records, 13 input features and one target). The source is the UCI Machine Learning Repository:

- Dataset page: <https://archive.ics.uci.edu/dataset/45/heart+disease>
- Original Cleveland file: `processed.cleveland.data`

Download that file from the dataset page and save it as `data/heart.csv`. The training script accepts the original comma-separated file (no header) with `?` markers for missing values. It also accepts a CSV with the exact canonical header:

`age,sex,cp,trestbps,chol,fbs,restecg,thalach,exang,oldpeak,slope,ca,thal,target`

The original target is 0–4; training maps 0 to the negative class and 1–4 to the positive class, following the UCI dataset description. Rows with missing values are removed and their count is reported. The downloaded data is excluded from version control.

The dataset is a small, historical research dataset, not a representative contemporary clinical cohort. This application is educational and is not suitable for diagnosis or treatment decisions.
