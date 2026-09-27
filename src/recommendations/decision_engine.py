import pandas as pd

inv_rec = pd.read_csv("../../data/processed/inventory_recommendations.csv")
order_rec = pd.read_csv("../../data/processed/order_recommendations.csv")
current_inv = pd.read_csv("../../data/raw/fact_inventory.csv", parse_dates=["date"])

latest_stock = (
    current_inv.sort_values("date")
    .groupby(["store_id", "product_id"])
    .tail(1)
)

merged = inv_rec.merge(
    latest_stock[["store_id", "product_id", "closing_stock"]],
    on=["store_id", "product_id"]
)

merged = merged.merge(
    order_rec[["store_id", "product_id", "recommended_order_qty"]],
    on=["store_id", "product_id"]
)

def decide(row):
    if row.closing_stock < row.reorder_point and row.recommended_order_qty > 0:
        return f"ORDER {int(row.recommended_order_qty)} UNITS"
    elif row.closing_stock > row.reorder_point * 2.5:
        return "REDUCE FUTURE ORDERS (overstock)"
    else:
        return "HOLD"

merged["decision"] = merged.apply(decide, axis=1)

merged[
    ["store_id", "product_id", "closing_stock", "reorder_point", "decision"]
].to_csv(
    "../../reports/decision_recommendations.csv",
    index=False
)

print(
    merged[
        ["store_id", "product_id", "closing_stock",
         "reorder_point", "decision"]
    ].head(20)
)