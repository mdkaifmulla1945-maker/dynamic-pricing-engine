from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import os
import logging
import traceback

from src.optimizer import PriceOptimizer

# =========================
# INIT APP
# =========================
app = FastAPI(title="Dynamic Pricing Engine")

logging.basicConfig(level=logging.INFO)

# =========================
# LOAD MODEL SAFELY
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "pricing_model.pkl")

try:
    model = joblib.load(MODEL_PATH)
    logging.info("Model loaded successfully")
except Exception as e:
    logging.error("Model loading failed")
    logging.error(traceback.format_exc())
    raise e

# =========================
# INIT OPTIMIZER
# =========================
optimizer = PriceOptimizer(model)

# =========================
# REQUEST SCHEMA
# =========================
class PricingRequest(BaseModel):
    store_id: int
    sku_id: int
    base_price: float
    is_featured_sku: int
    is_display_sku: int
    month: int
    year: int

    # safe defaults
    inventory: int = 50
    competitor_price: float = 100.0
    demand_pressure: float = 0.5

# =========================
# HEALTH CHECK
# =========================
@app.get("/")
def home():
    return {
        "status": "running",
        "service": "Dynamic Pricing Engine"
    }

# =========================
# CORE ENDPOINT
# =========================
@app.post("/optimize-price")
def optimize_price(req: PricingRequest):

    try:
        # convert request to dict
        data = req.dict()

        # enforce safe feature map (MATCH TRAINING FEATURES)
        features = {
            "store_id": data["store_id"],
            "sku_id": data["sku_id"],
            "total_price": data["base_price"],   # important mapping
            "base_price": data["base_price"],
            "is_featured_sku": data["is_featured_sku"],
            "is_display_sku": data["is_display_sku"],
            "month": data["month"],
            "year": data["year"],
            "inventory": data.get("inventory", 50),
            "competitor_price": data.get("competitor_price", 100.0),
            "demand_pressure": data.get("demand_pressure", 0.5),
        }

        # run optimizer
        result = optimizer.optimize(features)

        logging.info(f"Optimization success: {result}")

        return {
            "status": "success",
            "optimal_price": float(result.get("optimal_price", 0)),
            "expected_revenue": float(result.get("expected_revenue", 0))
        }

    except Exception as e:
        logging.error("API CRASH")
        logging.error(traceback.format_exc())

        return {
            "status": "error",
            "message": str(e)
        }