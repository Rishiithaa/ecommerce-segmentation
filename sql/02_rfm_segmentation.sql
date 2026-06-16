-- ============================================================
-- 02_rfm_segmentation.sql
-- RFM Model using NTILE(5) window functions
-- Scores every customer across Recency, Frequency, Monetary
-- then maps composite score → named segment
-- ============================================================

-- ─── Step 1: Raw RFM scores per customer ──────────────────
WITH rfm_raw AS (
    SELECT
        customer_id,
        country,
        acquisition_channel,
        recency_days,
        frequency,
        monetary_value,
        -- Lower recency = more recent = BETTER → reverse order
        NTILE(5) OVER (ORDER BY recency_days  DESC)   AS r_score,
        NTILE(5) OVER (ORDER BY frequency     ASC)    AS f_score,
        NTILE(5) OVER (ORDER BY monetary_value ASC)   AS m_score
    FROM mv_customer_metrics
),

-- ─── Step 2: Composite score + raw segment buckets ────────
rfm_scored AS (
    SELECT
        *,
        (r_score + f_score + m_score)               AS rfm_total,
        CONCAT(r_score::TEXT, f_score::TEXT, m_score::TEXT) AS rfm_cell
    FROM rfm_raw
),

-- ─── Step 3: Map scores → named segments ──────────────────
rfm_segmented AS (
    SELECT
        *,
        CASE
            -- Champion: bought recently, buys often, spends most
            WHEN r_score = 5 AND f_score >= 4 AND m_score >= 4
                THEN 'Champion'

            -- Loyal Customers: frequent buyers with solid spend
            WHEN f_score >= 4 AND m_score >= 3
                THEN 'Loyal Customer'

            -- Potential Loyalist: recent, average frequency
            WHEN r_score >= 4 AND f_score BETWEEN 2 AND 4
                THEN 'Potential Loyalist'

            -- Recent Customer: bought recently but infrequent
            WHEN r_score >= 4 AND f_score <= 2
                THEN 'New Customer'

            -- Promising: above-average recency, low frequency
            WHEN r_score = 3 AND f_score <= 2
                THEN 'Promising'

            -- Need Attention: above average RFM but slipping
            WHEN r_score = 3 AND f_score = 3 AND m_score = 3
                THEN 'Need Attention'

            -- At Risk: used to purchase often/spend a lot but haven't lately
            WHEN r_score <= 2 AND (f_score >= 3 OR m_score >= 3)
                THEN 'At-Risk'

            -- Cannot Lose Them: made large purchases, haven't returned
            WHEN r_score = 1 AND f_score >= 4
                THEN 'Cannot Lose Them'

            -- Hibernating: low R, low F, some spend
            WHEN r_score <= 2 AND f_score <= 2 AND m_score >= 2
                THEN 'Hibernating'

            -- Lost: low across all dimensions
            ELSE 'Lost'
        END AS segment
    FROM rfm_scored
)

-- ─── Final output ─────────────────────────────────────────
SELECT
    customer_id,
    country,
    acquisition_channel,
    recency_days,
    frequency,
    ROUND(monetary_value, 2)    AS monetary_value,
    r_score,
    f_score,
    m_score,
    rfm_total,
    rfm_cell,
    segment
FROM rfm_segmented
ORDER BY rfm_total DESC;


-- ============================================================
-- Segment Summary  |  Revenue & count per segment
-- ============================================================
WITH rfm_final AS (
    -- (paste the full CTE chain above, or reference a view)
    SELECT * FROM rfm_segmented   -- replace with full CTEs in production
)
SELECT
    segment,
    COUNT(*)                                        AS customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS pct_of_customers,
    ROUND(SUM(monetary_value), 2)                   AS total_revenue,
    ROUND(SUM(monetary_value) * 100.0
          / SUM(SUM(monetary_value)) OVER(), 2)     AS pct_of_revenue,
    ROUND(AVG(monetary_value), 2)                   AS avg_ltv,
    ROUND(AVG(recency_days),  1)                    AS avg_recency_days,
    ROUND(AVG(frequency),     1)                    AS avg_frequency
FROM rfm_final
GROUP BY segment
ORDER BY total_revenue DESC;


-- ============================================================
-- At-Risk Revenue Recovery  |  Quantify the opportunity
-- ============================================================
WITH rfm_final AS (SELECT * FROM rfm_segmented)
SELECT
    customer_id,
    country,
    ROUND(monetary_value, 2)        AS historical_spend,
    recency_days,
    frequency,
    -- Recoverable revenue = avg monthly spend × estimated recoverable months
    ROUND(
        (monetary_value / NULLIF(frequency, 0))
        * 3,   -- assume 3 re-engagement months
        2
    )                               AS estimated_recoverable_revenue
FROM rfm_final
WHERE segment = 'At-Risk'
ORDER BY estimated_recoverable_revenue DESC;
