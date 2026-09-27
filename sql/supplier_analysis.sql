-- Q6: Suppliers with poor delivery performance
SELECT * FROM v_supplier_performance ORDER BY on_time_delivery_pct ASC;