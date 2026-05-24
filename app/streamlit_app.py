import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import joblib
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.optimizer import PriceOptimizer

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Dynamic Pricing Engine",
    page_icon="💰",
    layout="centered"
)

# =========================
# PREMIUM UI THEME
# =========================
st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top, #0b1220, #05070f);
    color: #ffffff;
}

.block-container {
    padding: 2rem 2.5rem;
}

div[data-testid="metric-container"] {
    background: linear-gradient(145deg, #111827, #0b1220);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 18px;
    border-radius: 16px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.5);
    transition: 0.3s ease;
}

div[data-testid="metric-container"]:hover {
    transform: scale(1.04);
}

.stButton button {
    background: linear-gradient(90deg, #2563eb, #7c3aed);
    color: white;
    border-radius: 10px;
    padding: 0.6rem 1.2rem;
    border: none;
    font-weight: 600;
}

.stButton button:hover {
    transform: scale(1.05);
}

h1, h2, h3 {
    color: #ffffff;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


# =========================
# LOAD MODEL
# =========================
model = joblib.load("models/pricing_model.pkl")
optimizer = PriceOptimizer(model)

# =========================
# HEADER
# =========================
st.markdown("# 💰 Dynamic Pricing Control Center")
st.markdown("### AI Revenue Optimization Engine")
st.markdown("---")

# =========================
# LOAD DATA (SAFE)
# =========================
df = pd.read_csv("data/train.csv")

# FIX DATE COLUMN SAFELY
if "week" in df.columns:
    df["week"] = pd.to_datetime(
        df["week"],
        dayfirst=True,
        errors="coerce"
)

    df = df.dropna(subset=["week"])
    if df.empty:
       st.error("Dataset is empty after date processing")
       st.stop()


# =========================
# SESSION STATE
# =========================
if "row_index" not in st.session_state:
    st.session_state.row_index = 0

row_index = min(st.session_state.row_index, len(df) - 1)
row = df.iloc[row_index]

max_index = len(df) - 1


# =========================
# CURRENT ROW (SAFE ACCESS)
# =========================
row = df.iloc[row_index]

store_id = int(row.get("store_id", 0))
sku_id = int(row.get("sku_id", 0))
base_price = float(row.get("base_price", 0))
is_featured = int(row.get("is_featured_sku", 0))
is_display = int(row.get("is_display_sku", 0))

month = int(row["week"].month)
year = int(row["week"].year)

# =========================
# NAVIGATION
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("⬅ Previous"):
        if st.session_state.row_index > 0:
            st.session_state.row_index -= 1

with col2:
    st.markdown(f"### Product {st.session_state.row_index + 1} / {len(df)}")

with col3:
    if st.button("Next ➜"):
        if st.session_state.row_index < max_index:
            st.session_state.row_index += 1

st.markdown("---")

# =========================
# RUN MODEL
# =========================
if st.button("🚀 Get Optimal Price"):

    payload = {
        "store_id": store_id,
        "sku_id": sku_id,
        "base_price": base_price,
        "is_featured_sku": is_featured,
        "is_display_sku": is_display,
        "month": month,
        "year": year,
        "inventory": 50,
        "competitor_price": 100.0,
        "demand_pressure": 0.5
    }

    try:
        with st.spinner("🧠 AI is analyzing pricing strategy..."):
            result = optimizer.optimize(payload)

        # =========================
        # KPI DASHBOARD
        # =========================
        st.markdown("## 📊 Revenue Intelligence Dashboard")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("💰 Optimal Price", f"₹{result['optimal_price']}")

        with col2:
            st.metric("📈 Expected Revenue", f"₹{result['expected_revenue']}")

        with col3:
            efficiency = result["expected_revenue"] / max(result["optimal_price"], 1)
            st.metric("⚡ Efficiency", f"{efficiency:.2f}")

        st.markdown("---")

        # =========================
        # DECISION ENGINE
        # =========================
        st.markdown("## 🧠 AI Pricing Decision")

        if result["optimal_price"] > base_price:
            st.success("📈 Strong Demand → Increase Price")
        elif result["optimal_price"] < base_price:
            st.warning("📉 Price Sensitive Market → Discount Suggested")
        else:
            st.info("⚖️ Stable Market → Hold Price")

        st.markdown("---")

        # =========================
        # GRAPH
        # =========================
        st.markdown("## 📈 Optimization Curve")

        optimal = result["optimal_price"]

        prices = np.linspace(optimal * 0.7, optimal * 1.3, 25)
        revenues = [p * (result["expected_revenue"] / max(optimal, 1)) for p in prices]

        fig, ax = plt.subplots()
        ax.plot(prices, revenues, linewidth=3, color="#7c3aed")
        ax.scatter([optimal], [result["expected_revenue"]], color="#22c55e", s=120)

        ax.set_title("Revenue Optimization Curve")
        ax.set_xlabel("Price")
        ax.set_ylabel("Revenue")
        ax.grid(True, alpha=0.2)

        st.pyplot(fig)

        

    except Exception as e:
        st.error(f"Connection Error: {e}")