#  1. นำเข้าข้อมูล
import pandas as pd
data = pd.read_csv('train.csv')
testdata = pd.read_csv('test.csv')

# 2. แปลงคอลัมน์ Date ให้อยู่ในรูปแบบ dd/mm/yyyy
data['Date'] = pd.to_datetime(data['Date'],format='%d/%m/%Y')
testdata['Date'] = pd.to_datetime(testdata['Date'],format='%d/%m/%Y')

# 3. สร้างคุณลักษณะจากเวลา (Feature Engineering)
data['year'] = data['Date'].dt.year
data['month'] = data['Date'].dt.month
data['day'] = data['Date'].dt.day
data['weekday'] = data['Date'].dt.weekday
data = data.drop(columns=['Date'])

testdata['year'] = testdata['Date'].dt.year
testdata['month'] = testdata['Date'].dt.month
testdata['day'] = testdata['Date'].dt.day
testdata['weekday'] = testdata['Date'].dt.weekday
testdata = testdata.drop(columns=['Date'])

# 4. แปลงข้อมูลประเภทข้อความ (แปลง Object เป็น ตัวเลข bool)
data = pd.get_dummies(data,columns=['ProductName'], drop_first=True)
testdata = pd.get_dummies(testdata,columns=['ProductName'], drop_first=True)
actual_df = data[['year', 'month', 'day', 'Product categories', 'Sales']
                 ].rename(columns={'Sales': 'Actual_Sales'})

# 5. แยก x / y, Sales = ค่าที่ต้องการทำนาย

x = data.drop(columns=['Sales'])
y = data['Sales']

# 6. Train / Test Split
from sklearn.model_selection import train_test_split

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)    # แบ่ง train 80, test 20
testdata = testdata.reindex(columns=x.columns, fill_value=0)    # ทำให้ test มี column เหมือน train

# 7. Train model
# 7.1   ใช้ RandomForestRegressor สำหรับ Sales Forecasting
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

rf = RandomForestRegressor(n_estimators=200, random_state=42)
rf.fit(x_train, y_train)
rf_pred = rf.predict(x_test)
print("RandomForest")
print("MAE:", mean_absolute_error(y_test, rf_pred))
print("RMSE:", np.sqrt(mean_squared_error(y_test, rf_pred)))
print("R²:", r2_score(y_test, rf_pred))

# 7.2   ใช้ xgboost สำหรับ Sales Forecasting
from xgboost import XGBRegressor

xgb = XGBRegressor(
    n_estimators=300,     # จำนวนต้นไม้
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,        # สัดส่วนต่อหนึ่งต้นไม้
    colsample_bytree=0.8,
    random_state=42
)

xgb.fit(x_train, y_train)
xgb_pred = xgb.predict(x_test)

print("XGBoost")
print("MAE:", mean_absolute_error(y_test, xgb_pred))
print("RMSE:", np.sqrt(mean_squared_error(y_test, xgb_pred)))
print("R²:", r2_score(y_test, xgb_pred))