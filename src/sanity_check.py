import pandas as pd
sales = pd.read_csv("data/raw/fact_sales.csv")
inv = pd.read_csv("data/raw/fact_inventory.csv")

print(sales.groupby(sales["promotion_id"].notna())["quantity"].mean())  # promo qty should be higher
print(f"Stockout rate: {inv['stockout_flag'].mean()*100:.2f}%")          # expect ~20-25%