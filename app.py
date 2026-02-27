import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import bcrypt

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(page_title="Sales Forecast Dashboard", layout="wide")

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
        conn.execute("INSERT INTO users(username,password_hash) VALUES(?,?)", (user, hashb))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate(user: str, pwd: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT password_hash FROM users WHERE username=?", (user,)).fetchone()
    conn.close()
    if not row:
        return False
    return bcrypt.checkpw(pwd.encode(), row[0].encode())

def logout():
    if st.sidebar.button('Logout'):
        st.session_state.logged_in = False
        st.session_state.username = ''
        st.rerun()

def require_login():
    if not st.session_state.get('logged_in', False):
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
# DASHBOARD PAGE
# ======================
if page == 'Dashboard':
    require_login()
    st.title('📊 Dashboard')

    # Pivot Table
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

    # Donut Pie
    st.subheader('Product share (Donut Pie)')
    prod = st.selectbox('Select product', yearly['ProductName'].unique())
    pie_data = yearly[yearly['ProductName'] == prod][['Year','Sales']]
    fig_pie = go.Figure(go.Pie(labels=pie_data['Year'], values=pie_data['Sales'], hole=0.4))
    st.plotly_chart(fig_pie, use_container_width=True)

    # Quarterly Chart
    st.subheader('Quarterly Sales Trend')
    quarterly = (
        historical
        .assign(Quarter=historical['Date'].dt.to_period('Q').dt.strftime("Q%q-%Y"))
        .groupby(['Quarter'])['Sales']
        .sum()
        .reset_index()
    )
    fig_quarter = go.Figure(go.Bar(x=quarterly['Quarter'], y=quarterly['Sales'], name="Quarterly Sales"))
    fig_quarter.update_layout(xaxis_title="Quarter", yaxis_title="Sales")
    st.plotly_chart(fig_quarter, use_container_width=True)

    logout()

# ======================
# MAIN PAGE (FORECAST)
# ======================
if page == 'Main':
    st.title("📈 Sales Forecast Overview")

    st.subheader("Forecasted Monthly Sales")
    fig_forecast = go.Figure()
    for p in forecast['Product'].unique():
        fdata = forecast[forecast['Product'] == p]
        fig_forecast.add_trace(go.Scatter(
            x=fdata['Date'],
            y=fdata['Predicted_Sales'],
            mode='lines+markers',
            name=p
        ))
    fig_forecast.update_layout(xaxis_title="Month", yaxis_title="Predicted Sales")
    st.plotly_chart(fig_forecast, use_container_width=True)
