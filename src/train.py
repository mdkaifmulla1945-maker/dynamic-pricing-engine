import pandas as pd
import numpy as np
import joblib
import os

from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split

from sklearn.metrics import mean_absolute_error


# =========================
# CREATE FOLDER (if not exists)
# =========================
os.makedirs("models", exist_ok=True)


# =========================
# LOAD DATA
# =========================
df = pd.read_csv("data/train.csv")


# =========================
# DATE CLEANING (FIX FORMAT ISSUE)
# =========================

# Standardize date format
df['week'] = df['week'].astype(str).str.replace('/', '-', regex=False)

# Parse date safely
df['week'] = pd.to_datetime(df['week'], format='%d-%m-%Y', errors='coerce')


# =========================
# FEATURE ENGINEERING
# =========================

# Extract date features
df['year'] = df['week'].dt.year
df['month'] = df['week'].dt.month

# Discount feature
df["discount"] = df["base_price"] - df["total_price"]


# =========================
# PHASE 2: BUSINESS SIGNALS
# =========================

# Simulated inventory (if not present in dataset)
df["inventory"] = np.random.randint(10, 200, size=len(df))

# Simulated competitor price (important for pricing intelligence)
# =========================
# COMPETITOR PRICE (STABLE VERSION)
# =========================

np.random.seed(42)

df["competitor_price"] = df["base_price"] * (
    1 + np.random.normal(0, 0.05, size=len(df))
)

# Demand pressure (simple proxy signal)
df["demand_pressure"] = df["units_sold"] / (df["inventory"] + 1)

# Drop unnecessary columns
df = df.drop(['week', 'record_ID'], axis=1)


# =========================
# FEATURE SELECTION
# =========================

features = [
    "store_id",
    "sku_id",
    "total_price",
    "base_price",
    "is_featured_sku",
    "is_display_sku",
    "month",
    "year",
    "discount",
    "inventory",
    "competitor_price",
    "demand_pressure"
]

X = df[features]

# ✅ TARGET (FIXED)
y = df["units_sold"]


# =========================
# TRAIN TEST SPLIT
# =========================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)


# =========================
# MODEL TRAINING
# =========================


model = XGBRegressor(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)

# =========================
# TRAIN MODEL (MISSING PART FIX)
# =========================
print("Training model...")

model.fit(X_train, y_train)

print("Model training completed")

# =========================
# TEST SAMPLE PREDICTION
# =========================
print("Train sample prediction check:")

sample_pred = model.predict(X_train[:5])
print(sample_pred)


# =========================
# EVALUATION
# =========================
y_pred = model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)

print(f"Model MAE: {mae:.4f}")


# =========================
# SAVE MODEL
# =========================
joblib.dump(model, "models/pricing_model.pkl")

print("✅ Model saved at: models/pricing_model.pkl")