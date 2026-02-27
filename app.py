import streamlit as st
import pandas as pd
import plotly.graph_objects as go

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
    .sidebar .sidebar-content { background-color: #f7f7f8; }
    .stButton>button { background-color:#4CAF50; color:white; }
    .stTextInput>div>div>input { border-radius: 5px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------
# authentication helpers (database-backed)
# ----------------------
import sqlite3
import bcrypt

DB_PATH = 'users.db'

# initialize user database file

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

# make sure DB file is created on startup
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


def logout():
    if st.sidebar.button('Logout'):
        st.session_state.logged_in = False
        st.session_state.username = ''
        st.rerun()   # ใช้ st.rerun() แทน st.experimental_rerun()


# require login for dashboard pages

def require_login():
    if not st.session_state.get('logged_in', False):
        signup_form()
        login_form()
        st.stop()


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

# ----------------------
# page selector
# ----------------------
page = st.sidebar.selectbox('Go to', ['Main','Dashboard'])


# ======================
# MONTHLY AGGREGATION (HISTORICAL)
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

# ======================
# GLOBAL MONTHLY WEATHER
# ======================
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

# ----------------------
# handle pages
# ----------------------
if page == 'Dashboard':
    require_login()
    st.title('Dashboard')
    # yearly sales by product
    yearly = (
        historical
        .assign(Year=historical['Date'].dt.year)
        .groupby(['Year','ProductName'])['Sales']
        .sum()
        .reset_index()
    )
    st.subheader('Annual Sales by Product')
    st.dataframe(yearly)

    st.subheader('Product share (pie/donut)')
    prod = st.selectbox('Select product', yearly['ProductName'].unique())
    pie_data = yearly[yearly['ProductName'] == prod][['Year','Sales']]
    fig_pie = go.Figure(go.Pie(
        labels=pie_data['Year'],
        values=pie_data['Sales'],
        hole=0.4
    ))
    st.plotly_chart(fig_pie, use_container_width=True)
    # logout button
    logout()
    st.stop()

# ======================
# SIDEBAR FILTERS
# ======================
st.sidebar.header("🧭 Filters")

products = sorted(forecast['Product'].unique())
selected_products = st.sidebar.multiselect(
    "Select Product",
    products,
    default=products
)

all_dates = pd.concat([
    historical_monthly['Date'],
    forecast['Date']
]).sort_values()

start_month, end_month = st.sidebar.slider(
    "Select Month Range",
    min_value=all_dates.min().to_pydatetime(),
    max_value=all_dates.max().to_pydatetime(),
    value=(
        all_dates.min().to_pydatetime(),
        all_dates.max().to_pydatetime()
    ),
    format="YYYY-MM"
)

# ======================
# FILTER DATA
# ======================
hist_f = historical_monthly[
    (historical_monthly['ProductName'].isin(selected_products)) &
    (historical_monthly['Date'] >= pd.Timestamp(start_month)) &
    (historical_monthly['Date'] <= pd.Timestamp(end_month))
]

fore_f = forecast[
    (forecast['Product'].isin(selected_products)) &
    (forecast['Date'] >= pd.Timestamp(start_month)) &
    (forecast['Date'] <= pd.Timestamp(end_month))
]

weather_f = weather_monthly[
    (weather_monthly['Date'] >= pd.Timestamp(start_month)) &
    (weather_monthly['Date'] <= pd.Timestamp(end_month))
]

# ======================
# TABS
# ======================
tab1, tab2 = st.tabs([
    "📊 Sales: Historical vs Forecast",
    "🌦 Weather vs Sales"
])

# ======================================================
# TAB 1 : SALES
# ======================================================
with tab1:
    st.subheader("📈 Monthly Sales Comparison")

    fig = go.Figure()

    for p in selected_products:
        hist_p = hist_f[hist_f['ProductName'] == p]
        fore_p = fore_f[fore_f['Product'] == p]

        fig.add_trace(go.Scatter(
            x=hist_p['Date'],
            y=hist_p['Sales'],
            mode='lines+markers',
            name=f"{p} (Historical)"
        ))

        fig.add_trace(go.Scatter(
            x=fore_p['Date'],
            y=fore_p['Predicted_Sales'],
            mode='lines+markers',
            name=f"{p} (Forecast)",
            line=dict(dash='dash')
        ))

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Sales",
        legend_title="Product"
    )

    st.plotly_chart(fig, use_container_width=True)

# ======================================================
# TAB 2 : WEATHER vs SALES
# ======================================================
with tab2:
    st.subheader("🌦 Weather Factors vs Sales (Global Monthly)")

    weather_feature = st.selectbox(
        "Select Weather Variable",
        [
            "Cloud Coverage",
            "Temperature",
            "Wind Speed",
            "Weather Code",
            "Festival"
        ]
    )

    # Total Sales ต่อเดือน (ทุก Product)
    sales_monthly = (
        hist_f
        .groupby('Date')['Sales']
        .sum()
        .reset_index()
    )

    fig2 = go.Figure()

    # Sales
    fig2.add_trace(go.Bar(
        x=sales_monthly['Date'],
        y=sales_monthly['Sales'],
        name="Total Sales",
        opacity=0.6
    ))

    # Weather (single global line)
    fig2.add_trace(go.Scatter(
        x=weather_f['Date'],
        y=weather_f[weather_feature],
        name=weather_feature,
        yaxis="y2",
        mode="lines+markers",
        line=dict(width=3)
    ))

    fig2.update_layout(
        xaxis_title="Month",
        yaxis=dict(title="Sales"),
        yaxis2=dict(
            title=weather_feature,
            overlaying="y",
            side="right"
        ),
        legend=dict(x=0.01, y=0.99)
    )

    st.plotly_chart(fig2, use_container_width=True)

# ======================
# FOOTER
# ======================
st.caption(
    "Weather variables are treated as global exogenous factors aggregated monthly."
)
if page == 'Dashboard':
    require_login()
    st.title('Dashboard')

    # Annual Sales Pivot Table
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

    # Donut Pie Chart
    st.subheader('Product share (Donut Pie)')
    prod = st.selectbox('Select product', yearly['ProductName'].unique())
    pie_data = yearly[yearly['ProductName'] == prod][['Year','Sales']]
    fig_pie = go.Figure(go.Pie(
        labels=pie_data['Year'],
        values=pie_data['Sales'],
        hole=0.4
    ))
    st.plotly_chart(fig_pie, use_container_width=True)

    # Quarterly Sales Chart
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

    # ======================
    # Logout Button
    # ======================
    logout()
    st.stop()
