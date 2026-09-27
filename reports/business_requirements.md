# OptiChain — Business Requirements

## Business Problem
Retailers face a trade-off between maintaining sufficient inventory and
minimizing excess stock, while promotions and supplier reliability both
affect whether that inventory turns into profit.

## Objective
Build an analytical decision-support system that forecasts demand, evaluates
promotional effectiveness, optimizes replenishment, and evaluates supplier
performance.

## Analytical Questions
1. What drives product demand?
2. Which products/stores generate the most profit (not just revenue)?
3. Which promotions generate incremental profit, not just incremental sales?
4. Which products are at risk of stockout, and where is capital tied up in excess stock?
5. How much inventory should be ordered, and when?
6. Which suppliers provide reliable fulfillment, and at what cost trade-off?
7. How do changes in demand, pricing and lead time affect profitability? (what-if)

## Scope
- 12 stores, 60 products, 8 suppliers, 2 years daily data (start small; scale later)
- Synthetic data, generated with documented business logic, calibrated against
  patterns from public retail datasets (Rossmann, M5) rather than invented arbitrarily