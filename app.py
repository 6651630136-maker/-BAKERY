import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import bcrypt
import os
import requests

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(
    page_title="Sales Forecast Dashboard",
    layout="wide"
)

# basic styling tweaks
st.markdown(
    """
    <style>
    body {background-color: #fafafa;}
    .sidebar .sidebar-content { background-color: #f7f7f8; }
    .stButton>button { background-color:#4CAF50; color:white; }
    .stTextInput>div>div>input { border-radius: 5px; }
    .stTabs [role="tab"] { color: #333; font-weight:500; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ======================
# AUTHENTICATION HELPERS
# ======================
DB_PATH = 'users.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT
        )"""
    )
    conn.commit()
    conn.close()

init_db()

def register_user(user: str, pwd: str) -> bool:
    hashb = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO users(username,password_hash) VALUES(?,?)",
            (user, hashb),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate(user: str, pwd: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT password_hash FROM users WHERE username=?", (user,)
    ).fetchone()
    conn.close()
    if not row:
        return False
    return bcrypt.checkpw(pwd.encode(), row[0].encode())

def logout():
    if st.sidebar.button('Logout'):
        st.session_state.logged_in = False
        st.session_state.username = ''
        st.session_state.github_logged_in = False
        st.session_state.github_user = ''
        st.rerun()

def require_login():
    if not st.session_state.get('logged_in', False) and not st.session_state.get('github_logged_in', False):
        signup_form()
        login_form()
        st.stop()

def login_form():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ''
    with st.sidebar.form('login_form', clear_on_submit=False):
        st.write('### 🔐 Login')
        user = st.text_input('Username')
        pwd = st.text_input('Password', type='password')
        submitted = st.form_submit_button('Sign in')
        if submitted:
            if authenticate(user, pwd):
                st.session_state.logged_in = True
                st.session_state.username = user
                st.sidebar.success(f'Logged in as {user}')
            else:
                st.sidebar.error('Invalid credentials')

    st.sidebar.markdown('---')
    if not st.session_state.get('github_logged_in'):
        github_oauth_button()
    else:
        st.sidebar.success(f"Logged in via GitHub: {st.session_state.github_user}")

def signup_form():
    with st.sidebar.form('signup_form', clear_on_submit=True):
        st.write('### 📝 Register')
        user = st.text_input('Choose username')
        pwd = st.text_input('Choose password', type='password')
        submitted = st.form_submit_button('Sign up')
        if submitted:
            if register_user(user, pwd):
                st.sidebar.success('Account created. Please log in.')
            else:
                st.sidebar.error('Username already exists')

# ======================
# GITHUB OAUTH
# ======================
def github_oauth_button():
    CLIENT_ID = os.getenv('GITHUB_CLIENT_ID','')
    CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET','')
    redirect_uri = st.query_params.get('redirect_uri', '')

    params = {
        'client_id': CLIENT_ID,
        'scope': 'read:user user:email',
        'allow_signup': 'true',
        'redirect_uri': redirect_uri,
    }
    auth_url = 'https://github.com/login/oauth/authorize'
    st.sidebar.markdown(f"[Login with GitHub]({auth_url}?" + '&'.join(f"{k}={v}" for k,v in params.items()) + ")")

    qp = st.query_params
    if 'code' in qp:
        code = qp['code'][0] if isinstance(qp['code'], list) else qp['code']
        token_resp = requests.post(
            'https://github.com/login/oauth/access_token',
            headers={'Accept':'application/json'},
            data={
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'code': code
            }
        )
        data = token_resp.json()
        if 'access_token' in data:
            token = data['access_token']
            user_resp = requests.get('https://api.github.com/user',
                                     headers={'Authorization': f'token {token}'})
            user = user_resp.json()
            st.session_state.github_logged_in = True
            st.session_state.github_user = user.get('login')
            st.sidebar.success(f"GitHub: {user.get('login')}")
            st.query_params.clear()
        else:
            st.sidebar.error('GitHub login failed')

# ======================
# LOAD DATA
# ======================
try:
    historical = pd.read_csv("train.csv")
    forecast = pd.read_csv("monthly_forecast.csv")
except FileNotFoundError as e:
    st.error(f"❌ CSV file not found: {e}")
    st.stop()

historical['Date'] = pd.to_datetime(historical['Date'], dayfirst=True)
forecast['Date'] = pd.to_datetime(forecast['Date'])

# ======================
# PAGE SELECTOR
# ======================
page = st.sidebar.selectbox('Go to', ['Main','Dashboard'])

# ======================
# AGGREGATION
# ======================
historical['YearMonth'] = historical['Date'].dt.to_period('M').dt.to_timestamp()
historical_monthly = (
    historical
    .groupby(['ProductName', 'YearMonth'])
    .agg({
        'Sales': 'sum',
        'Cloud Coverage': 'mean',
        'Temperature': 'mean',
        'Wind Speed': 'mean',
        'Weather Code': 'mean',
        'Festival': 'max'
    })
    .reset_index()
    .rename(columns={'YearMonth': 'Date'})
)

weather_monthly = (
    historical_monthly
    .groupby('Date')
    .agg({
        'Cloud Coverage': 'mean',
        'Temperature': 'mean',
        'Wind Speed': 'mean',
        'Weather Code': 'mean',
        'Festival': 'max'
    })
    .reset_index()
)

# ======================
# DASHBOARD PAGE
# ======================
if page == 'Dashboard':
    require_login()
    st.title('Dashboard')

    yearly = (
        historical
        .assign(Year=historical['Date'].dt.year)
        .groupby(['Year','ProductName'])['Sales']
        .sum()
        .reset_index()
    )
    st.subheader('Annual Sales by Product (Pivot Table)')
    pivot = pd.pivot_table(yearly, values='Sales', index='Year', columns='ProductName', aggfunc='sum')
    st.dataframe(pivot)

    st.subheader('Product share (Donut Pie)')
    prod = st.selectbox('Select product', yearly['ProductName'].unique())
    pie_data = yearly[yearly['ProductName'] == prod][['Year','Sales']]
    fig_pie = go.Figure(go.Pie(
        labels=pie_data['Year'],
        values=pie_data['Sales'],
        hole=0.4
    ))
    st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader('Quarterly Sales Trend')
    quarterly = (
        historical
        .assign(Quarter=historical['Date'].dt.to_period('Q').dt.strftime("Q%q-%Y"))
        .groupby(['Quarter'])['Sales']
        .sum()
        .reset_index()
    )
    fig_quarter = go.Figure(go.Bar(
        x=quarterly['Quarter'],
        y=quarterly['Sales'],
        name="Quarterly Sales"
    ))
    fig_quarter.update_layout(xaxis_title="Quarter", yaxis_title="Sales")
    st.plotly_chart(fig_quarter, use_container_width=True)

    logout()
    st.stop()
