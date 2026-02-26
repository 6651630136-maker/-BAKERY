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

# ======================
# LOAD DATA
# ======================
historical = pd.read_csv("train.csv")
forecast = pd.read_csv("monthly_forecast.csv")

historical['Date'] = pd.to_datetime(historical['Date'], dayfirst=True)
forecast['Date'] = pd.to_datetime(forecast['Date'])

# ======================
# MONTHLY AGGREGATION (HISTORICAL)
# ======================
historical_monthly = (
    historical
    .assign(Date=historical['Date'].dt.to_period('M').dt.to_timestamp())
    .groupby(['ProductName', 'Date'])
    .agg({
        'Sales': 'sum',
        'Cloud Coverage': 'mean',
        'Temperature': 'mean',
        'Wind Speed': 'mean',
        'Weather Code': 'mean',
        'Festival': 'max'
    })
    .reset_index()
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
