import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="OptiChain What-If Simulator", layout="wide")
st.title("OptiChain — What-If Simulator")

product = pd.read_csv("data/raw/dim_product.csv")
sales = pd.read_csv("data/processed/fact_sales_clean.csv", parse_dates=["date"])

col1, col2 = st.columns(2)
with col1:
    demand_growth = st.slider("Expected demand growth (%)", -20, 50, 10) / 100
    discount = st.slider("Discount (%)", 0, 40, 15) / 100
with col2:
    lead_time = st.slider("Supplier lead time (days)", 1, 15, 5)
    service_level = st.slider("Service level (%)", 80, 99, 95) / 100

pid = st.selectbox("Product", product["product_id"])
row = product[product.product_id == pid].iloc[0]
prod_sales = sales[sales.product_id == pid]

base_demand = prod_sales["quantity"].mean()
sigma_d = prod_sales["quantity"].std()

# elasticity assumption — document this like you did in the generator
ELASTICITY = 1.5
adj_demand = base_demand * (1 + demand_growth) * (1 + ELASTICITY * discount)

from scipy.stats import norm
z = norm.ppf(service_level)
safety_stock = z * sigma_d * np.sqrt(lead_time)
reorder_point = adj_demand * lead_time + safety_stock

sell_price = row.selling_price * (1 - discount)
revenue = adj_demand * sell_price * 30   # monthly projection
profit = adj_demand * (sell_price - row.cost_price) * 30

st.subheader("Projected outcomes")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Monthly Revenue", f"₹{revenue:,.0f}")
c2.metric("Monthly Profit", f"₹{profit:,.0f}")
c3.metric("Safety Stock", f"{safety_stock:.0f} units")
c4.metric("Reorder Point", f"{reorder_point:.0f} units")

st.caption("Elasticity and lead-time assumptions are illustrative — documented in methodology.md")