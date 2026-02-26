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

### Authentication & extra dashboard

The app now includes a simple **login/logout** form in the sidebar backed by a SQLite database. You can register a new account via the sidebar.

If you prefer a built-in demo user instead, the credentials `admin` / `password` will also work (this user is created automatically).


After logging in, you can choose **Dashboard** from the sidebar menu. The
Dashboard page shows:

* yearly sales table for each product
* pie/donut chart of sales share per year for a selected product

This new page is separate from the original filters/plots, which remain same.

---

## Optional backend / OAuth example

The `backend/` folder contains a minimal FastAPI application configured for
GitHub OAuth. It is *not required* for the Streamlit front end but can be used
to offload authentication or connect to a PostgreSQL database.

### Running the backend locally

1. Fill in `.env` with your GitHub app credentials and database URL.
2. Install backend deps (same `requirements.txt` covers them) and run:

   ```bash
   uvicorn backend.app:app --reload
   ```

3. Visit `http://localhost:8000/login/github` to initiate GitHub login flow.

The code stores OAuth tokens in memory (for demonstration only). You can
modify `backend/app.py` to persist users in PostgreSQL using `psycopg2` or
SQLAlchemy.

### Using OAuth in Streamlit

Modify `login_form()` in `app.py` to call your backend endpoint, e.g.: 

```python
import requests

def authenticate(user, pwd):
    r = requests.post('http://localhost:8000/authenticate', json={'user':user,'pwd':pwd})
    return r.json().get('ok', False)
```

or load a token cookie returned by the backend and verify it locally.

### PostgreSQL instead of SQLite

Set `DATABASE_URL` in `.env` then replace SQLite functions with a connection
helper:

```python
def get_conn():
    return psycopg2.connect(os.environ['DATABASE_URL'])
```

Use this helper in `register_user()` and `authenticate()`.

---

## Theming and layout tips

- Customize colors via CSS in `st.markdown` or a `config.toml` theme.
- Use `st.columns()`/`st.expander()` for complex layouts.
- For interactive tables, consider [`streamlit-aggrid`](https://github.com/PablocFonseca/streamlit-aggrid).

---

## Large files & Git LFS

To track CSVs with Git LFS:

```bash
git lfs install
git lfs track "*.csv"
git add .gitattributes
# re-add csvs so they go through LFS
```