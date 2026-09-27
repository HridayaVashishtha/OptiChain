-- Q1: High revenue but low profit products (margin erosion — discounting too much?)
SELECT product_id,
       SUM(revenue) AS total_revenue,
       SUM(profit) AS total_profit,
       ROUND(SUM(profit)/NULLIF(SUM(revenue),0), 4) AS margin_pct
FROM fact_sales
GROUP BY product_id
HAVING SUM(revenue) > (SELECT AVG(rev) FROM (SELECT SUM(revenue) rev FROM fact_sales GROUP BY product_id) t)
ORDER BY margin_pct ASC
LIMIT 15;


-- Q4: Fastest growing categories (this year's H2 vs H1)
SELECT p.category,
       SUM(CASE WHEN s.date < '2024-07-01' THEN s.revenue ELSE 0 END) AS h1_revenue,
       SUM(CASE WHEN s.date >= '2024-07-01' THEN s.revenue ELSE 0 END) AS h2_revenue,
       ROUND((SUM(CASE WHEN s.date >= '2024-07-01' THEN s.revenue ELSE 0 END)
            - SUM(CASE WHEN s.date < '2024-07-01' THEN s.revenue ELSE 0 END))
            / NULLIF(SUM(CASE WHEN s.date < '2024-07-01' THEN s.revenue ELSE 0 END),0), 4) AS growth_pct
FROM fact_sales s JOIN dim_product p ON p.product_id = s.product_id
GROUP BY p.category
ORDER BY growth_pct DESC;