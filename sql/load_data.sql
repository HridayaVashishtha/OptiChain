\copy dim_supplier    FROM 'data/raw/dim_supplier.csv'  WITH (FORMAT csv, HEADER true);
\copy dim_product     FROM 'data/raw/dim_product.csv'   WITH (FORMAT csv, HEADER true);
\copy dim_store       FROM 'data/raw/dim_store.csv'     WITH (FORMAT csv, HEADER true);
\copy dim_date        FROM 'data/raw/dim_date.csv'      WITH (FORMAT csv, HEADER true);
\copy fact_promotions FROM 'data/raw/fact_promotions.csv' WITH (FORMAT csv, HEADER true);

-- fact_sales.csv has a transaction_id column, but the table column is BIGSERIAL —
-- load through a staging table so Postgres generates fresh IDs cleanly.
CREATE TEMP TABLE stg_sales (
    transaction_id BIGINT, date DATE, store_id VARCHAR, product_id VARCHAR,
    quantity INT, selling_price NUMERIC, discount_pct NUMERIC,
    revenue NUMERIC, cost NUMERIC, profit NUMERIC, promotion_id VARCHAR
);
\copy stg_sales FROM 'data/processed/fact_sales_clean.csv' WITH (FORMAT csv, HEADER true);

INSERT INTO fact_sales (date, store_id, product_id, quantity, selling_price, discount_pct, revenue, cost, profit, promotion_id)
SELECT date, store_id, product_id, quantity, selling_price, discount_pct, revenue, cost, profit, NULLIF(promotion_id,'')
FROM stg_sales;

\copy fact_inventory FROM 'data/raw/fact_inventory.csv' WITH (FORMAT csv, HEADER true);
\copy fact_orders    FROM 'data/raw/fact_orders.csv'    WITH (FORMAT csv, HEADER true);
\copy fact_supplier_deliveries FROM 'data/raw/fact_supplier_deliveries.csv' WITH (FORMAT csv, HEADER true);