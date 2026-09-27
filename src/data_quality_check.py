import pandas as pd

RAW = "data/raw"
sales = pd.read_csv(f"{RAW}/fact_sales_dirty.csv")
orders = pd.read_csv(f"{RAW}/fact_orders.csv")
deliveries = pd.read_csv(f"{RAW}/fact_supplier_deliveries.csv")
inv = pd.read_csv(f"{RAW}/fact_inventory.csv")

report = []
raw_records = len(sales)
report.append(("Raw fact_sales records", raw_records))

dupes = sales.duplicated(subset=["date", "store_id", "product_id", "transaction_id"]).sum()
report.append(("Duplicate transaction records", dupes))

invalid_price = (sales["selling_price"] <= 0).sum()
report.append(("Invalid (<=0) selling prices", invalid_price))

negative_qty = (sales["quantity"] < 0).sum()
report.append(("Negative quantities", negative_qty))

missing_supplier = orders["supplier_id"].isna().sum()
report.append(("Orders missing supplier_id", missing_supplier))

neg_inventory = (inv["closing_stock"] < 0).sum()
report.append(("Negative closing_stock records", neg_inventory))

final_usable = raw_records - dupes - invalid_price - negative_qty

print(f"{'Check':45s} {'Count':>12s}")
print("-" * 58)
for name, val in report:
    print(f"{name:45s} {val:>12,}")
print("-" * 58)
print(f"{'Final usable fact_sales records':45s} {final_usable:>12,}")