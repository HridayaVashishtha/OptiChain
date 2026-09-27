-- ============================================================
-- OptiChain — PostgreSQL Schema
-- ============================================================

DROP TABLE IF EXISTS fact_supplier_deliveries CASCADE;
DROP TABLE IF EXISTS fact_orders CASCADE;
DROP TABLE IF EXISTS fact_promotions CASCADE;
DROP TABLE IF EXISTS fact_inventory CASCADE;
DROP TABLE IF EXISTS fact_sales CASCADE;
DROP TABLE IF EXISTS dim_product CASCADE;
DROP TABLE IF EXISTS dim_store CASCADE;
DROP TABLE IF EXISTS dim_supplier CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;

-- ---------- DIMENSION TABLES ----------

CREATE TABLE dim_supplier (
    supplier_id         VARCHAR(10) PRIMARY KEY,
    supplier_name       VARCHAR(100) NOT NULL,
    category            VARCHAR(50),
    base_lead_time_days INT CHECK (base_lead_time_days >= 0),
    defect_rate_base    NUMERIC(5,4) DEFAULT 0
);

CREATE TABLE dim_product (
    product_id          VARCHAR(10) PRIMARY KEY,
    product_name        VARCHAR(150) NOT NULL,
    category            VARCHAR(50),
    subcategory         VARCHAR(50),
    brand               VARCHAR(50),
    cost_price          NUMERIC(12,2) CHECK (cost_price >= 0),
    selling_price       NUMERIC(12,2) CHECK (selling_price >= 0),
    launch_date         DATE,
    primary_supplier_id VARCHAR(10) REFERENCES dim_supplier(supplier_id)
);

CREATE TABLE dim_store (
    store_id    VARCHAR(10) PRIMARY KEY,
    city        VARCHAR(50),
    region      VARCHAR(20),
    store_type  VARCHAR(20),
    floor_area  INT
);

CREATE TABLE dim_date (
    date          DATE PRIMARY KEY,
    year          INT,
    month         INT,
    week          INT,
    day_of_week   VARCHAR(10),
    is_weekend    BOOLEAN,
    is_holiday    BOOLEAN
);

-- ---------- FACT TABLES ----------

CREATE TABLE fact_promotions (
    promotion_id   VARCHAR(10) PRIMARY KEY,
    product_id     VARCHAR(10) REFERENCES dim_product(product_id),
    start_date     DATE,
    end_date       DATE,
    discount_pct   NUMERIC(5,4),
    campaign_type  VARCHAR(50),
    marketing_cost NUMERIC(12,2),
    channel        VARCHAR(50),
    CHECK (end_date >= start_date)
);

CREATE TABLE fact_sales (
    transaction_id BIGSERIAL PRIMARY KEY,
    date           DATE REFERENCES dim_date(date),
    store_id       VARCHAR(10) REFERENCES dim_store(store_id),
    product_id     VARCHAR(10) REFERENCES dim_product(product_id),
    quantity       INT CHECK (quantity >= 0),
    selling_price  NUMERIC(12,2),
    discount_pct   NUMERIC(5,4) DEFAULT 0,
    revenue        NUMERIC(14,2),
    cost           NUMERIC(14,2),
    profit         NUMERIC(14,2),
    promotion_id   VARCHAR(10) REFERENCES fact_promotions(promotion_id)
);
CREATE INDEX idx_sales_date ON fact_sales(date);
CREATE INDEX idx_sales_store_product ON fact_sales(store_id, product_id);

CREATE TABLE fact_inventory (
    date            DATE REFERENCES dim_date(date),
    store_id        VARCHAR(10) REFERENCES dim_store(store_id),
    product_id      VARCHAR(10) REFERENCES dim_product(product_id),
    opening_stock   INT,
    received        INT,
    sold            INT,
    closing_stock   INT,
    stockout_flag   BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (date, store_id, product_id)
);
CREATE INDEX idx_inv_store_product ON fact_inventory(store_id, product_id);

CREATE TABLE fact_orders (
    order_id           VARCHAR(15) PRIMARY KEY,
    supplier_id         VARCHAR(10) REFERENCES dim_supplier(supplier_id),
    store_id            VARCHAR(10) REFERENCES dim_store(store_id),
    product_id          VARCHAR(10) REFERENCES dim_product(product_id),
    order_date          DATE,
    quantity_ordered    INT CHECK (quantity_ordered > 0),
    expected_delivery   DATE
);

CREATE TABLE fact_supplier_deliveries (
    order_id           VARCHAR(15) PRIMARY KEY REFERENCES fact_orders(order_id),
    supplier_id        VARCHAR(10) REFERENCES dim_supplier(supplier_id),
    promised_date      DATE,
    actual_date        DATE,
    quantity_ordered   INT,
    quantity_received  INT,
    defect_units       INT DEFAULT 0
);

-- ---------- ANALYTICAL VIEWS ----------

CREATE OR REPLACE VIEW v_supplier_performance AS
SELECT
    d.supplier_id,
    s.supplier_name,
    COUNT(*) AS total_deliveries,
    ROUND(AVG(CASE WHEN d.actual_date <= d.promised_date THEN 1.0 ELSE 0 END), 4) AS on_time_delivery_pct,
    ROUND(SUM(d.quantity_received)::numeric / NULLIF(SUM(d.quantity_ordered),0), 4) AS fill_rate,
    ROUND(STDDEV(d.actual_date - d.promised_date), 2) AS lead_time_variability_days,
    ROUND(SUM(d.defect_units)::numeric / NULLIF(SUM(d.quantity_received),0), 4) AS defect_rate
FROM fact_supplier_deliveries d
JOIN dim_supplier s ON s.supplier_id = d.supplier_id
GROUP BY d.supplier_id, s.supplier_name;

CREATE OR REPLACE VIEW v_inventory_kpis AS
SELECT
    store_id, product_id,
    ROUND(AVG(closing_stock), 1) AS avg_inventory,
    SUM(sold) AS total_units_sold,
    ROUND(AVG(CASE WHEN stockout_flag THEN 1.0 ELSE 0 END), 4) AS stockout_rate
FROM fact_inventory
GROUP BY store_id, product_id;