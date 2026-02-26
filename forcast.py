import pandas as pd
from xgboost import XGBRegressor

# ======================
# LOAD DATA
# ======================
data = pd.read_csv("train.csv")
data['Date'] = pd.to_datetime(data['Date'], format='%d/%m/%Y')

# ======================
# FEATURE ENGINEERING
# ======================
data['year'] = data['Date'].dt.year
data['month'] = data['Date'].dt.month
data['day'] = data['Date'].dt.day
data['weekday'] = data['Date'].dt.weekday

# เก็บชื่อ product ไว้ก่อน
data['Product'] = data['ProductName']

# One-hot product
data = pd.get_dummies(data, columns=['ProductName'], drop_first=True)

# ======================
# DEFINE FEATURES
# ======================
weather_features = [
    'Cloud Coverage',
    'Temperature',
    'Wind Speed',
    'Weather Code',
    'Festival'
]

x = data.drop(columns=['Sales', 'Date', 'Product'])
y = data['Sales']

# ======================
# TRAIN MODEL
# ======================
model = XGBRegressor(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)
model.fit(x, y)

# ======================
# FEATURE IMPORTANCE (Weather)
# ======================
importance = pd.DataFrame({
    'Feature': x.columns,
    'Importance': model.feature_importances_
})

weather_importance = (
    importance[importance['Feature'].isin(weather_features)]
    .sort_values(by='Importance', ascending=False)
)

weather_importance.to_csv(
    "feature_importance.csv",
    index=False
)

# ======================
# CREATE FUTURE DATES (1 YEAR)
# ======================
future_dates = pd.date_range(
    start=data['Date'].max() + pd.Timedelta(days=1),
    periods=365,
    freq='D'
)

future_base = pd.DataFrame({
    'year': future_dates.year,
    'month': future_dates.month,
    'day': future_dates.day,
    'weekday': future_dates.weekday
})

# ใช้ค่าเฉลี่ย weather จากอดีต (มาตรฐานงานวิจัย)
weather_means = data[weather_features].mean()

for col in weather_features:
    future_base[col] = weather_means[col]

# ======================
# CREATE FUTURE DATA PER PRODUCT
# ======================
product_cols = [c for c in x.columns if c.startswith('ProductName_')]
rows = []

for p in product_cols:
    temp = future_base.copy()
    for col in product_cols:
        temp[col] = 1 if col == p else 0

    temp['Product'] = p.replace('ProductName_', '')
    rows.append(temp)

future_df = pd.concat(rows, ignore_index=True)

# จัด column ให้ตรงกับตอน train
future_df = future_df.reindex(columns=x.columns.tolist() + ['Product'], fill_value=0)

# ======================
# PREDICT
# ======================
x_future = future_df[x.columns]
future_df['Predicted_Sales'] = model.predict(x_future)

future_df['Date'] = pd.to_datetime(
    future_df[['year', 'month', 'day']]
)

# ======================
# MONTHLY AGGREGATION
# ======================
monthly_forecast = (
    future_df
    .groupby(
        ['Product', future_df['Date'].dt.to_period('M')]
    )['Predicted_Sales']
    .sum()
    .reset_index()
)

monthly_forecast.columns = ['Product', 'Date', 'Predicted_Sales']
monthly_forecast['Date'] = monthly_forecast['Date'].astype(str)

monthly_forecast.to_csv("monthly_forecast.csv", index=False)

print("✅ monthly_forecast.csv created")
print("✅ feature_importance.csv created")