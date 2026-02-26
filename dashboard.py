import pandas as pd
from xgboost import XGBRegressor

# =========================
# LOAD & PREPARE TRAINING DATA
# =========================
# dashboard.py is meant to be run standalone so we need to recreate
# the training environment (same preprocessing as the forecasting script).
# read the historical dataset and build the feature matrix used by the model.

data = pd.read_csv("train.csv")
# convert the date string to datetime (day/month/year format)
data['Date'] = pd.to_datetime(data['Date'], format='%d/%m/%Y')

# feature engineering: extract date parts
for col in ['year', 'month', 'day', 'weekday']:
    data[col] = getattr(data['Date'].dt, col)

# save product name separately for later use
data['Product'] = data['ProductName']

# one‑hot encode the product and drop the original column
data = pd.get_dummies(data, columns=['ProductName'], drop_first=True)

# define feature matrix and target
x = data.drop(columns=['Sales', 'Date', 'Product'])
y = data['Sales']

# train a fresh xgboost model (same hyperparameters used elsewhere)
xgb = XGBRegressor(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)
xgb.fit(x, y)

# =========================
# CREATE FUTURE DATE RANGE (1 YEAR)
# =========================
last_date = pd.to_datetime(
    data[['year','month','day']]
    .assign(Date=lambda x: pd.to_datetime(x[['year','month','day']]))
    ['Date']
).max()

future_dates = pd.date_range(
    start=last_date + pd.Timedelta(days=1),
    periods=365,
    freq='D'
)

future_df = pd.DataFrame({'Date': future_dates})

# Feature engineering
future_df['year'] = future_df['Date'].dt.year
future_df['month'] = future_df['Date'].dt.month
future_df['day'] = future_df['Date'].dt.day
future_df['weekday'] = future_df['Date'].dt.weekday

# =========================
# CREATE FUTURE DATA PER PRODUCT
# =========================
product_cols = [c for c in x.columns if c.startswith('ProductName_')]

future_all = []

for product_col in product_cols:
    temp = future_df.copy()

    # one-hot encode product
    for col in product_cols:
        temp[col] = 1 if col == product_col else 0

    # ใส่ชื่อสินค้า (สำคัญมาก)
    temp['Product'] = product_col.replace('ProductName_', '')

    future_all.append(temp)

future_predict_df = pd.concat(future_all, ignore_index=True)

# ให้ column ตรงกับ model
future_predict_df = future_predict_df.reindex(
    columns=x.columns.tolist() + ['Product'],
    fill_value=0
)

# =========================
# PREDICT
# =========================
future_predict_df['Predicted_Sales'] = xgb.predict(
    future_predict_df[x.columns]
)

# =========================
# MONTHLY AGGREGATION
# =========================
monthly_forecast = (
    future_predict_df
    .groupby(['Product', 'year', 'month'])['Predicted_Sales']
    .sum()
    .reset_index()
)

# สร้าง Date สำหรับ dashboard
monthly_forecast['Date'] = pd.to_datetime(
    monthly_forecast[['year','month']].assign(day=1)
)

monthly_forecast = monthly_forecast.sort_values(['Product', 'Date'])

# =========================
# SAVE FILE
# =========================
monthly_forecast.to_csv("monthly_forecast.csv", index=False)

print("✅ monthly_forecast.csv created successfully")
print(monthly_forecast.head())
