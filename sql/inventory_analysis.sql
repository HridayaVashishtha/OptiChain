-- Q2: Stores with unusually high stockout rates
SELECT store_id, ROUND(AVG(CASE WHEN stockout_flag THEN 1.0 ELSE 0 END), 4) AS stockout_rate
FROM fact_inventory
GROUP BY store_id
ORDER BY stockout_rate DESC;


-- Q3: Overstocked products (high avg inventory, low turnover)
SELECT i.product_id,
       ROUND(AVG(i.closing_stock), 1) AS avg_inventory,
       SUM(s.quantity) AS units_sold,
       ROUND(AVG(i.closing_stock) / NULLIF(SUM(s.quantity), 0), 3) AS inventory_to_sales_ratio
FROM fact_inventory i
LEFT JOIN fact_sales s ON s.product_id = i.product_id AND s.date = i.date AND s.store_id = i.store_id
GROUP BY i.product_id
ORDER BY inventory_to_sales_ratio DESC
LIMIT 15;


-- Q7: Rising demand but shrinking inventory (early warning for stockouts)
SELECT s.product_id,
       SUM(CASE WHEN s.date >= '2024-10-01' THEN s.quantity ELSE 0 END) AS recent_demand,
       SUM(CASE WHEN s.date < '2024-10-01' THEN s.quantity ELSE 0 END) AS prior_demand,
       (SELECT AVG(closing_stock) FROM fact_inventory i WHERE i.product_id = s.product_id AND i.date >= '2024-10-01') AS recent_avg_stock
FROM fact_sales s
GROUP BY s.product_id
HAVING SUM(CASE WHEN s.date >= '2024-10-01' THEN s.quantity ELSE 0 END)
     > SUM(CASE WHEN s.date < '2024-10-01' THEN s.quantity ELSE 0 END)
ORDER BY recent_demand DESC
LIMIT 15;


-- Q8: High inventory, low sales stores (capital tied up)
WITH inventory_summary AS (
    SELECT
        store_id,
        ROUND(AVG(closing_stock), 1) AS avg_inventory
    FROM fact_inventory
    GROUP BY store_id
),
sales_summary AS (
    SELECT
        store_id,
        SUM(revenue) AS revenue
    FROM fact_sales
    GROUP BY store_id
)
SELECT
    i.store_id,
    i.avg_inventory,
    s.revenue
FROM inventory_summary i
LEFT JOIN sales_summary s
    ON i.store_id = s.store_id
ORDER BY i.avg_inventory DESC, s.revenue ASC;