import numpy as np
import pandas as pd

# =========================
# PRICE OPTIMIZER v3 (CLEAN + STABLE)
# =========================

class PriceOptimizer:

    def __init__(self, model):
        self.model = model

    # -------------------------
    # CORE OPTIMIZATION
    # -------------------------
    def optimize(self, data):

        base = float(data["base_price"])
        competitor = float(data["competitor_price"])
        inventory = float(data["inventory"])

        # =========================
        # PRICE RANGE ENGINE
        # =========================
        min_price = max(base * 0.6, competitor * 0.8)
        max_price = min(base * 1.4, competitor * 1.2)

        steps = 30 if inventory > 100 else 20

        prices = np.linspace(min_price, max_price, steps)

        best_price = base
        best_score = -1

        # =========================
        # ITERATE PRICES
        # =========================
        for price in prices:

            discount = base - price

            row = pd.DataFrame([{
                "store_id": data["store_id"],
                "sku_id": data["sku_id"],
                "total_price": price,
                "base_price": base,
                "is_featured_sku": data["is_featured_sku"],
                "is_display_sku": data["is_display_sku"],
                "month": data["month"],
                "year": data["year"],
                "discount": discount,
                "inventory": inventory,
                "competitor_price": competitor,
                "demand_pressure": data["demand_pressure"]
            }])

            # =========================
            # MODEL PREDICTION
            # =========================
            try:
                pred = self.model.predict(row)[0]
            except Exception:
                pred = 0

            # If model trained on log target
            # MODEL PREDICTION (RAW SCORE)
            try:
               pred = self.model.predict(row)[0]
            except Exception:
               pred = 0

# SAFE DEMAND CONVERSION (NO LOG ASSUMPTION)
            demand = max(pred, 0)

# prevent zero collapse
            demand = max(demand, 0.1)

            print("RAW PRED:", pred, "DEMAND:", demand)

            # =========================
            # REVENUE CALC
            # =========================
            # realistic demand scaling (prevents fake flat revenue)
            demand = max(demand, 0.1)

            # price sensitivity penalty (real-world behavior)
            price_factor = 1 / (1 + abs(price - base) / base)

            revenue = price * demand * price_factor
            # =========================
            # BUSINESS PENALTIES
            # =========================

            penalty = 0

            # competitor constraint
            if price > competitor:
                penalty += 0.08 * revenue

            # stock pressure (safe scaling)
            if inventory < 20:
                penalty += 0.05 * revenue

            # demand surge control
            if demand > 100:
                penalty += 0.1 * revenue

            score = revenue - penalty

            if score > best_score:
                best_score = score
                best_price = price

        # =========================
        # OUTPUT
        # =========================
        return {
            "optimal_price": round(float(best_price), 2),
            "expected_revenue": round(float(best_score), 2)
        }