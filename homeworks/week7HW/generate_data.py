"""
Generate the homework dataset: orders.csv — a realistic online-store order log.

Deterministic (fixed seed) so the analysis has reproducible answers. Real signal
is baked in on purpose:
  - revenue peaks in Nov/Dec (holiday season)
  - Electronics is the highest-revenue category
  - higher discounts drive a higher refund/cancel rate (a real correlation to find)

Run once to (re)create orders.csv:
    python3 generate_data.py
"""

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
N = 6000

categories = {
    "Electronics": (120, 900),
    "Home":        (25, 250),
    "Clothing":    (15, 120),
    "Books":       (8, 45),
    "Toys":        (10, 90),
}
cat_names = list(categories)
cat_weights = [0.28, 0.22, 0.25, 0.13, 0.12]
countries = ["US", "UK", "DE", "FR", "TR", "NL", "ES"]
country_weights = [0.34, 0.16, 0.14, 0.11, 0.1, 0.08, 0.07]

# Dates across 2023-2024, weighted so Nov/Dec are busier (holiday peak).
month_weight = np.array([0.6, 0.6, 0.8, 0.8, 0.9, 0.9, 0.9, 0.9, 1.0, 1.1, 1.6, 1.8])
month_weight = month_weight / month_weight.sum()

rows = []
for i in range(N):
    year = rng.choice([2023, 2024])
    month = rng.choice(range(1, 13), p=month_weight)
    day = rng.integers(1, 28)
    cat = rng.choice(cat_names, p=cat_weights)
    lo, hi = categories[cat]
    unit_price = round(float(rng.uniform(lo, hi)), 2)
    qty = int(rng.integers(1, 6))
    discount = int(rng.choice([0, 5, 10, 15, 20, 30, 40],
                              p=[0.30, 0.18, 0.18, 0.13, 0.1, 0.07, 0.04]))

    # Refund/cancel probability RISES with discount (the correlation to discover),
    # with a small category effect (Clothing gets returned more).
    base = 0.04 + discount * 0.006 + (0.05 if cat == "Clothing" else 0.0)
    r = rng.random()
    if r < base * 0.6:
        status = "refunded"
    elif r < base:
        status = "cancelled"
    else:
        status = "completed"

    rows.append({
        "order_id": 100000 + i,
        "order_date": f"{year}-{month:02d}-{day:02d}",
        "customer_id": int(rng.integers(1, 1500)),
        "country": rng.choice(countries, p=country_weights),
        "category": cat,
        "unit_price": unit_price,
        "quantity": qty,
        "discount_pct": discount,
        "status": status,
    })

df = pd.DataFrame(rows).sort_values("order_date").reset_index(drop=True)
df.to_csv("orders.csv", index=False)
print(f"Wrote orders.csv: {len(df)} rows")
print(df["status"].value_counts())
print("Categories:", df["category"].value_counts().to_dict())