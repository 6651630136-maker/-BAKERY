import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(page_title="Sales Forecast Dashboard", layout="wide")

# ======================
# LOAD DATA
# ======================
try:
    historical = pd.read_csv("train.csv")
    forecast = pd.read_csv("monthly_forecast.csv")
except FileNotFoundError as e:
    st.error(f"❌ CSV file not found: {e}")
    st.stop()

# Convert date columns
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
    st.title('Dashboard')

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
