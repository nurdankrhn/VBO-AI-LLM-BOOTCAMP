# Orders Analysis Report

## Dataset Profile

**Row Count:** 6,000 orders

**Date Range:** 2023-01-01 to 2024-12-27

**Order Status Distribution:**
- Completed: 5,356 orders
- Refunded: 389 orders
- Cancelled: 255 orders

---

## Question 1: Highest Completed-Order Revenue Month

**Result:** November 2023 (2023-11) had the highest completed-order revenue at **$245,728.354**

**Conclusion:** November 2023 was the peak revenue month for completed orders. This analysis filtered exclusively for orders with "completed" status and calculated revenue using the formula: unit_price × quantity × (1 - discount_pct / 100).

---

## Question 2: Category with Most Completed-Order Revenue

**Result:** **Electronics** generated the most completed-order revenue with **$2,112,140.5985**

**Conclusion:** Electronics is the dominant revenue-generating category, producing more than 4.7 times the revenue of the second-place category (Home). This analysis was based exclusively on completed orders, demonstrating Electronics' strong market performance.

---

## Question 3: Refund/Cancellation Rate by Discount Level

**Refund/Cancellation Rates by Discount Percentage:**

| Discount % | Refund/Cancel Rate | Count |
|------------|-------------------|-------|
| 0% | 4.49% | 82 of 1,827 |
| 5% | 5.38% | 56 of 1,040 |
| 10% | 11.02% | 119 of 1,080 |
| 15% | 15.52% | 120 of 773 |
| 20% | 16.42% | 101 of 615 |
| 30% | 22.04% | 95 of 431 |
| 40% | 30.34% | 71 of 234 |

**Conclusion:** There is a **strong positive trend** between discount percentage and refund/cancellation rate. The correlation is 0.9905, indicating that orders with higher discounts are significantly more likely to be refunded or cancelled. The rate increases from 4.49% at 0% discount to 30.34% at 40% discount, suggesting that deeper discounts may attract less committed customers or indicate problematic products.

---

## Question 4: Top 3 Countries by Completed-Order Revenue

**Results:**

1. **US:** $1,008,048.95
2. **DE (Germany):** $452,360.71
3. **UK:** $444,536.92

**Conclusion:** The United States dominates completed-order revenue, generating more than double the revenue of Germany (the second-place country). These three countries account for the majority of completed-order revenue, with the US being the clear market leader.

---

## Question 5: Percentage of Revenue Lost to Refunds/Cancellations

**Result:** **8.72%** of potential revenue was lost to refunded and cancelled orders

**Details:**
- Refunded/Cancelled Revenue: $280,253.15
- Total Revenue (All Orders): $3,213,184.50
- Percentage Lost: 8.721975031476381%

**Conclusion:** Approximately 8.72% of potential revenue is lost due to refunded and cancelled orders. This represents a significant financial impact of $280,253.15 across the dataset. The analysis used the revenue formula (unit_price × quantity × (1 - discount_pct/100)) for all orders regardless of status, then calculated the proportion attributable to failed orders.

---

## Summary

The orders dataset reveals several key business insights:

1. **Seasonal Performance:** November 2023 was the peak revenue month, suggesting seasonal demand patterns worth investigating further.

2. **Category Concentration:** Electronics dominates revenue generation, indicating a strong product-market fit in this category.

3. **Discount Risk:** Higher discounts correlate strongly with refunds and cancellations, suggesting the need for more selective discount strategies.

4. **Geographic Focus:** The US market is the primary revenue driver, with Germany and UK as secondary markets.

5. **Revenue Loss:** Nearly 9% of potential revenue is lost to refunds and cancellations, representing a material business impact that warrants investigation into root causes.
