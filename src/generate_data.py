"""
OptiChain synthetic data generator.
Every number comes from an explicit rule, not pure noise — documented here
so you can defend every assumption in an interview.
"""
import numpy as np
import pandas as pd
from datetime import date, timedelta
import os

rng = np.random.default_rng(42)

# ---------------- CONFIG ----------------
N_STORES = 12
N_PRODUCTS = 60
N_SUPPLIERS = 8
START_DATE = date(2024, 1, 1)
N_DAYS = 730  # 2 years
OUT_DIR = "data/raw"
os.makedirs(OUT_DIR, exist_ok=True)

CATEGORIES = {
    "Electronics": ("Mobile", "Laptop", "Accessories"),
    "Beauty":      ("Hair Care", "Skin Care", "Makeup"),
    "Grocery":     ("Snacks", "Beverages", "Staples"),
    "Apparel":     ("Men", "Women", "Kids"),
    "Home":        ("Kitchen", "Furnishing", "Decor"),
}
REGIONS = {"Mumbai": "West", "Pune": "West", "Delhi": "North",
           "Bengaluru": "South", "Chennai": "South", "Kolkata": "East"}
CITIES = list(REGIONS.keys())

# ---------------- DIM: SUPPLIER ----------------
supplier_rows = []
for i in range(N_SUPPLIERS):
    sid = f"SUP{i+1:02d}"
    cat = rng.choice(list(CATEGORIES.keys()))
    supplier_rows.append({
        "supplier_id": sid,
        "supplier_name": f"Supplier {chr(65+i)}",
        "category": cat,
        "base_lead_time_days": int(rng.integers(2, 10)),
        "defect_rate_base": round(rng.uniform(0.005, 0.04), 4),
        "_reliability": rng.uniform(0.55, 0.97),  # drives on-time probability, not exported
    })
dim_supplier = pd.DataFrame(supplier_rows)
supplier_reliability = dim_supplier.set_index("supplier_id")["_reliability"]
dim_supplier = dim_supplier.drop(columns=["_reliability"])

# ---------------- DIM: PRODUCT ----------------
product_rows = []
for i in range(N_PRODUCTS):
    pid = f"P{i+1:03d}"
    cat = rng.choice(list(CATEGORIES.keys()))
    subcat = rng.choice(CATEGORIES[cat])
    cost = round(float(rng.uniform(50, 40000)), 2) if cat == "Electronics" else round(float(rng.uniform(20, 3000)), 2)
    margin = rng.uniform(1.15, 1.45)
    price = round(cost * margin, 2)
    eligible = dim_supplier[dim_supplier.category == cat]
    supplier_id = (eligible.sample(1, random_state=int(rng.integers(0, 1e6)))["supplier_id"].values[0]
                   if len(eligible) else dim_supplier.sample(1)["supplier_id"].values[0])
    product_rows.append({
        "product_id": pid,
        "product_name": f"{subcat} Item {i+1}",
        "category": cat, "subcategory": subcat,
        "brand": f"Brand {rng.integers(1,15)}",
        "cost_price": cost, "selling_price": price,
        "launch_date": (START_DATE - timedelta(days=int(rng.integers(0, 900)))).isoformat(),
        "primary_supplier_id": supplier_id,
        "_base_demand": rng.uniform(2, 25),
        "_elasticity": rng.uniform(1.0, 2.5),
        "_seasonality_amp": rng.uniform(0.05, 0.35),
    })
dim_product = pd.DataFrame(product_rows)
gen_params = dim_product[["product_id", "_base_demand", "_elasticity", "_seasonality_amp"]].set_index("product_id")
dim_product = dim_product.drop(columns=["_base_demand", "_elasticity", "_seasonality_amp"])

# ---------------- DIM: STORE ----------------
store_rows = []
for i in range(N_STORES):
    city = CITIES[i % len(CITIES)]
    store_rows.append({
        "store_id": f"S{i+1:03d}", "city": city, "region": REGIONS[city],
        "store_type": rng.choice(["Small", "Medium", "Large"], p=[0.3, 0.4, 0.3]),
        "floor_area": int(rng.integers(5000, 20000)),
        "_store_factor": rng.uniform(0.6, 1.6),
    })
dim_store = pd.DataFrame(store_rows)
store_factor = dim_store.set_index("store_id")["_store_factor"]
dim_store = dim_store.drop(columns=["_store_factor"])

# ---------------- DIM: DATE ----------------
dates = [START_DATE + timedelta(days=i) for i in range(N_DAYS)]
HOLIDAYS = {(1,26), (8,15), (10,2), (12,25), (11,1), (10,24)}
dim_date = pd.DataFrame({
    "date": [d.isoformat() for d in dates],
    "year": [d.year for d in dates], "month": [d.month for d in dates],
    "week": [d.isocalendar()[1] for d in dates],
    "day_of_week": [d.strftime("%A") for d in dates],
    "is_weekend": [d.weekday() >= 5 for d in dates],
    "is_holiday": [(d.month, d.day) in HOLIDAYS for d in dates],
})

# ---------------- FACT: PROMOTIONS ----------------
promo_rows, promo_lookup, ctr = [], {}, 1
for pid in dim_product.product_id:
    for _ in range(rng.integers(3, 8)):
        off = int(rng.integers(0, N_DAYS - 14))
        start_d = dates[off]
        end_d = min(start_d + timedelta(days=int(rng.integers(3, 10))), dates[-1])
        discount = float(rng.choice([0.05, 0.10, 0.15, 0.20, 0.25, 0.30]))
        pcode = f"PR{ctr:04d}"; ctr += 1
        promo_rows.append({"promotion_id": pcode, "product_id": pid,
            "start_date": start_d.isoformat(), "end_date": end_d.isoformat(),
            "discount_pct": discount,
            "campaign_type": rng.choice(["Flash Sale", "Seasonal", "Clearance", "Festival"]),
            "marketing_cost": round(float(rng.uniform(2000, 50000)), 2),
            "channel": rng.choice(["In-store", "App Push", "Email", "Social"])})
        d_iter = start_d
        while d_iter <= end_d:
            promo_lookup[(pid, d_iter)] = (pcode, discount)
            d_iter += timedelta(days=1)
fact_promotions = pd.DataFrame(promo_rows)

# ---------------- FACT: SALES + INVENTORY + ORDERS (day-by-day simulation) ----------------
prod_supplier = dim_product.set_index("product_id")["primary_supplier_id"]
prod_price = dim_product.set_index("product_id")[["cost_price", "selling_price"]]
supplier_lead = dim_supplier.set_index("supplier_id")["base_lead_time_days"]

stock = {(s, p): int(rng.integers(40, 150)) for s in dim_store.store_id for p in dim_product.product_id}
pending = {}          # (store,product) -> day order is due, if one's in flight
scheduled = {}         # (day, store, product) -> qty arriving that day
sales_rows, inv_rows = [], []
order_rows, delivery_rows = [], []
txn_id, order_ctr = 1, 1
REORDER_POINT_FACTOR, REORDER_QTY_FACTOR = 4, 12

for day_idx, d in enumerate(dates):
    dow_factor = 1.15 if d.weekday() >= 5 else 1.0
    holiday_factor = 1.4 if (d.month, d.day) in HOLIDAYS else 1.0
    season_phase = 2 * np.pi * (day_idx % 365) / 365.0

    for pid in dim_product.product_id:
        base, elast, seas_amp = gen_params.loc[pid, ["_base_demand", "_elasticity", "_seasonality_amp"]]
        seas = 1 + seas_amp * np.sin(season_phase + hash(pid) % 6)
        cost, price = prod_price.loc[pid, "cost_price"], prod_price.loc[pid, "selling_price"]
        promo = promo_lookup.get((pid, d))
        pcode, discount = (promo[0], promo[1]) if promo else (None, 0.0)
        uplift = 1 + elast * discount if promo else 1.0

        for sid in dim_store.store_id:
            sf = store_factor.loc[sid]
            expected = base * seas * dow_factor * holiday_factor * uplift * sf
            demand = max(0, int(rng.poisson(max(expected, 0.1))))
            opening = stock[(sid, pid)]
            sold = min(demand, opening)
            stockout = demand > opening

            received = scheduled.pop((day_idx, sid, pid), 0)
            if received > 0:
                pending[(sid, pid)] = None
            closing = opening - sold + received
            stock[(sid, pid)] = closing

            rop = REORDER_POINT_FACTOR * base
            if closing < rop and pending.get((sid, pid)) is None:
                supplier_id = prod_supplier.loc[pid]
                lead = int(supplier_lead.loc[supplier_id])
                order_qty = int(REORDER_QTY_FACTOR * base * rng.uniform(0.85, 1.15))
                arrival_day = day_idx + lead
                scheduled[(arrival_day, sid, pid)] = order_qty
                pending[(sid, pid)] = arrival_day

            sell_price = round(price * (1 - discount), 2)
            revenue, cost_total = round(sell_price * sold, 2), round(cost * sold, 2)
            if sold > 0:
                sales_rows.append({"transaction_id": txn_id, "date": d.isoformat(),
                    "store_id": sid, "product_id": pid, "quantity": sold,
                    "selling_price": sell_price, "discount_pct": discount,
                    "revenue": revenue, "cost": cost_total, "profit": round(revenue - cost_total, 2),
                    "promotion_id": pcode})
                txn_id += 1
            inv_rows.append({"date": d.isoformat(), "store_id": sid, "product_id": pid,
                "opening_stock": opening, "received": received, "sold": sold,
                "closing_stock": closing, "stockout_flag": stockout})

fact_sales = pd.DataFrame(sales_rows)
fact_inventory = pd.DataFrame(inv_rows)

# ---------------- FACT: ORDERS + SUPPLIER DELIVERIES ----------------
recv = fact_inventory[fact_inventory.received > 0].copy()
recv["date"] = pd.to_datetime(recv["date"])
order_rows, delivery_rows = [], []
for _, row in recv.iterrows():
    pid, sid, recv_date, qty = row.product_id, row.store_id, row.date, row.received
    supplier_id = prod_supplier.loc[pid]
    lead = int(supplier_lead.loc[supplier_id])
    reliability = supplier_reliability.loc[supplier_id]
    defect_base = dim_supplier.set_index("supplier_id").loc[supplier_id, "defect_rate_base"]

    order_date = recv_date - timedelta(days=lead)
    expected_delivery = order_date + timedelta(days=lead)
    oid = f"O{order_ctr:06d}"; order_ctr += 1
    order_rows.append({"order_id": oid, "supplier_id": supplier_id, "store_id": sid,
        "product_id": pid, "order_date": order_date.date().isoformat(),
        "quantity_ordered": int(qty), "expected_delivery": expected_delivery.date().isoformat()})

    if rng.random() < reliability:
        delay = int(rng.choice([-1, 0, 0], p=[0.15, 0.55, 0.30]))
    else:
        max_delay = int(np.round(2 + (1 - reliability) * 10))
        delay = int(rng.integers(1, max(2, max_delay)))
    actual_date = expected_delivery + timedelta(days=delay)
    defect_units = int(rng.binomial(qty, defect_base))
    shortfall = (1 - reliability) * 0.06
    qty_received = max(0, int(qty - rng.integers(0, max(1, int(qty * (0.02 + shortfall))))))
    delivery_rows.append({"order_id": oid, "supplier_id": supplier_id,
        "promised_date": expected_delivery.date().isoformat(), "actual_date": actual_date.date().isoformat(),
        "quantity_ordered": int(qty), "quantity_received": qty_received, "defect_units": defect_units})

fact_orders = pd.DataFrame(order_rows)
fact_supplier_deliveries = pd.DataFrame(delivery_rows)

# ---------------- WRITE ----------------
for name, df in [("dim_product", dim_product), ("dim_store", dim_store), ("dim_supplier", dim_supplier),
                  ("dim_date", dim_date), ("fact_sales", fact_sales), ("fact_inventory", fact_inventory),
                  ("fact_promotions", fact_promotions), ("fact_orders", fact_orders),
                  ("fact_supplier_deliveries", fact_supplier_deliveries)]:
    df.to_csv(f"{OUT_DIR}/{name}.csv", index=False)
    print(f"{name:28s} {len(df):>10,} rows")