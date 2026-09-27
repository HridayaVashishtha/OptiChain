-- Q5: Promotions with best incremental profit vs marketing cost
SELECT pr.promotion_id, pr.product_id, pr.marketing_cost,
       SUM(s.profit) AS promo_period_profit,
       ROUND((SUM(s.profit) - pr.marketing_cost) / NULLIF(pr.marketing_cost,0), 3) AS roi
FROM fact_promotions pr
JOIN fact_sales s ON s.promotion_id = pr.promotion_id
GROUP BY pr.promotion_id, pr.product_id, pr.marketing_cost
ORDER BY roi DESC
LIMIT 15;