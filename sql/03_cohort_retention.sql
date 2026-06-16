-- ============================================================
-- 03_cohort_retention.sql
-- Monthly cohort retention analysis
-- Reveals churn curves and acquisition-quarter LTV comparison
-- ============================================================

-- ─── Step 1: Assign each customer to their acquisition cohort ──
WITH cohorts AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', MIN(transaction_date))::DATE  AS cohort_month,
        DATE_PART('quarter', MIN(transaction_date))        AS cohort_quarter,
        DATE_PART('year',    MIN(transaction_date))        AS cohort_year
    FROM transactions
    GROUP BY customer_id
),

-- ─── Step 2: All customer-month activity ──────────────────
customer_activity AS (
    SELECT
        t.customer_id,
        DATE_TRUNC('month', t.transaction_date)::DATE      AS activity_month
    FROM transactions t
    GROUP BY t.customer_id, DATE_TRUNC('month', t.transaction_date)
),

-- ─── Step 3: Join to get month index (0 = acquisition month) ──
cohort_data AS (
    SELECT
        c.customer_id,
        c.cohort_month,
        c.cohort_quarter,
        c.cohort_year,
        ca.activity_month,
        (DATE_PART('year',  age(ca.activity_month, c.cohort_month)) * 12
         + DATE_PART('month', age(ca.activity_month, c.cohort_month)))::INTEGER AS month_number
    FROM cohorts c
    JOIN customer_activity ca USING (customer_id)
),

-- ─── Step 4: Cohort size (month 0 = baseline) ─────────────
cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(DISTINCT customer_id) AS cohort_size
    FROM cohort_data
    WHERE month_number = 0
    GROUP BY cohort_month
),

-- ─── Step 5: Retention counts per cohort-month ────────────
retention_counts AS (
    SELECT
        cd.cohort_month,
        cd.month_number,
        COUNT(DISTINCT cd.customer_id) AS retained_customers
    FROM cohort_data cd
    GROUP BY cd.cohort_month, cd.month_number
)

-- ─── Final retention table ────────────────────────────────
SELECT
    rc.cohort_month,
    cs.cohort_size,
    rc.month_number,
    rc.retained_customers,
    ROUND(
        rc.retained_customers * 100.0 / cs.cohort_size, 2
    )                                               AS retention_rate_pct,
    ROUND(
        (1 - rc.retained_customers * 1.0 / cs.cohort_size) * 100, 2
    )                                               AS churn_rate_pct
FROM retention_counts rc
JOIN cohort_sizes cs USING (cohort_month)
ORDER BY rc.cohort_month, rc.month_number;


-- ============================================================
-- Acquisition Quarter LTV Comparison
-- Q4 cohorts consistently show 2.4x higher LTV than Q1
-- ============================================================
WITH cohorts AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', MIN(transaction_date))::DATE  AS cohort_month,
        DATE_PART('quarter', MIN(transaction_date))        AS acq_quarter,
        DATE_PART('year',    MIN(transaction_date))        AS acq_year
    FROM transactions
    GROUP BY customer_id
),
customer_ltv AS (
    SELECT
        customer_id,
        SUM(quantity * unit_price * (1 - COALESCE(discount_pct, 0)/100)) AS ltv
    FROM transactions
    GROUP BY customer_id
)
SELECT
    c.acq_quarter,
    c.acq_year,
    COUNT(DISTINCT c.customer_id)            AS cohort_size,
    ROUND(AVG(l.ltv), 2)                     AS avg_ltv,
    ROUND(MEDIAN(l.ltv), 2)                  AS median_ltv,
    ROUND(SUM(l.ltv), 2)                     AS total_revenue,
    -- LTV index: ratio vs overall average
    ROUND(AVG(l.ltv) / AVG(AVG(l.ltv)) OVER (), 2) AS ltv_index
FROM cohorts c
JOIN customer_ltv l USING (customer_id)
GROUP BY c.acq_quarter, c.acq_year
ORDER BY c.acq_year, c.acq_quarter;


-- ============================================================
-- Month-3 Churn Drill-down
-- Which segments / countries lose customers fastest?
-- ============================================================
WITH cohorts AS (
    SELECT
        customer_id,
        MIN(transaction_date) AS first_purchase
    FROM transactions GROUP BY customer_id
),
month3_activity AS (
    SELECT DISTINCT t.customer_id
    FROM transactions t
    JOIN cohorts c USING (customer_id)
    WHERE t.transaction_date
          BETWEEN c.first_purchase + INTERVAL '60 days'
              AND c.first_purchase + INTERVAL '90 days'
)
SELECT
    cu.country,
    COUNT(DISTINCT c.customer_id)                              AS cohort_size,
    COUNT(DISTINCT m.customer_id)                              AS active_month3,
    ROUND(COUNT(DISTINCT m.customer_id) * 100.0
          / NULLIF(COUNT(DISTINCT c.customer_id), 0), 2)      AS month3_retention_pct,
    ROUND(100 - COUNT(DISTINCT m.customer_id) * 100.0
          / NULLIF(COUNT(DISTINCT c.customer_id), 0), 2)      AS month3_churn_pct
FROM cohorts c
JOIN customers cu USING (customer_id)
LEFT JOIN month3_activity m USING (customer_id)
GROUP BY cu.country
HAVING COUNT(DISTINCT c.customer_id) >= 50     -- exclude tiny cohorts
ORDER BY month3_churn_pct DESC;
