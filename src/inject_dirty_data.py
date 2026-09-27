import pandas as pd
import numpy as np

rng = np.random.default_rng(7)
RAW = "data/raw"

sales = pd.read_csv(f"{RAW}/fact_sales.csv")
dirty = sales.copy()

# 1) Duplicate ~0.4% of rows (double-counted POS transactions)
dupe_idx = rng.choice(dirty.index, size=int(len(dirty) * 0.004), replace=False)
dirty = pd.concat([dirty, dirty.loc[dupe_idx]], ignore_index=True)

# 2) Corrupt ~0.15% of selling_price to 0 or negative (entry errors)
bad_price_idx = rng.choice(dirty.index, size=int(len(dirty) * 0.0015), replace=False)
dirty.loc[bad_price_idx, "selling_price"] = rng.choice([0, -1], size=len(bad_price_idx))

# 3) Corrupt ~0.1% of quantity to negative (return/refund miscoding)
bad_qty_idx = rng.choice(dirty.index, size=int(len(dirty) * 0.001), replace=False)
dirty.loc[bad_qty_idx, "quantity"] = -dirty.loc[bad_qty_idx, "quantity"]

# 4) Null out ~0.3% of discount_pct (missing field on ingestion)
null_disc_idx = rng.choice(dirty.index, size=int(len(dirty) * 0.003), replace=False)
dirty.loc[null_disc_idx, "discount_pct"] = np.nan

dirty.to_csv(f"{RAW}/fact_sales_dirty.csv", index=False)
print(f"Clean: {len(sales):,} rows -> Dirty: {len(dirty):,} rows")