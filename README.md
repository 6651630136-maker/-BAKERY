# Bakery — Sales Forecast App

This repository contains a Streamlit app for bakery sales forecasting.

Files of interest
- `app.py` — Streamlit application entrypoint
- `requirements.txt` — Python dependencies used by Streamlit

Run locally

1. Create a Python environment and install dependencies:

```bash
python -m venv .venv
.\.venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

2. Start the app:

```bash
streamlit run app.py
```

Deploy to Streamlit Community Cloud

1. Make sure your repo is pushed to GitHub (public or private with access).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **New app** → select repository `6651630136-maker/-BAKERY`, branch `main`, and file `app.py` as the entrypoint. Click **Deploy**.

Once deployed, the app URL will be:

```
https://share.streamlit.io/6651630136-maker/-BAKERY/main/app.py
```

Notes
- If your CSV files are large, consider using Git LFS or hosting the data elsewhere to avoid slowing the repo.
- If Streamlit fails to install dependencies, check `requirements.txt` for correct package names.
