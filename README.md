# E-Commerce Customer Segmentation & Retention Analysis

![pipeline](https://github.com/rishiithaa/ecommerce-segmentation/actions/workflows/pipeline.yml/badge.svg)
![license](https://img.shields.io/badge/license-MIT-green)
![python](https://img.shields.io/badge/python-3.12-blue)

A complete end-to-end data analytics project analyzing 300,000+ transactions across 37 countries. The system segments customers using an RFM model built on PostgreSQL window functions, identifies at-risk revenue, and reveals cohort retention patterns to directly inform re-engagement campaigns.

**Stack:** PostgreSQL · Python (pandas, numpy) · Tableau · HTML/JS dashboard

---

## Key Findings

| Finding | Detail |
|---|---|
| **Champion revenue concentration** | Top 13% of customers (Champions) drove **53% of total revenue** ($23.3M) |
| **At-Risk opportunity** | 5,869 customers flagged with **$180K+ recoverable annual revenue** |
| **Month-3 churn wall** | **81% of customers churn by Month 3** — the critical retention window |
| **Q4 LTV advantage** | Q4-acquired customers show **2.72× higher LTV** vs Q1 ($1,646 vs $604) |

---

## Project Structure

```
ecommerce-segmentation/
├── sql/
│   ├── 01_schema.sql              # Database schema, indexes, materialized views
│   ├── 02_rfm_segmentation.sql    # RFM model with NTILE(5) window functions
│   └── 03_cohort_retention.sql    # Cohort analysis + quarter LTV comparison
│
├── python/
│   ├── generate_data.py           # Synthetic data generation + full Python analysis
│   └── tableau_prep.py            # Export clean CSVs for Tableau
│
├── dashboard/
│   └── index.html                 # Interactive HTML dashboard (Chart.js)
│
├── data/                          # Generated after running Python scripts
│   ├── customers.csv
│   ├── transactions.csv
│   ├── rfm_scores.csv
│   ├── segment_summary.csv
│   ├── cohort_matrix.csv
│   ├── tableau_rfm_customers.csv
│   ├── tableau_cohort_retention.csv
│   ├── tableau_monthly_revenue.csv
│   └── tableau_geo_summary.csv
│
├── docs/
│   └── tableau_setup.md           # Tableau worksheet-by-worksheet build guide
│
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Quickstart

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/ecommerce-segmentation.git
cd ecommerce-segmentation
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Generate the synthetic dataset and run RFM + cohort analysis

```bash
python python/generate_data.py
```

This generates 300K+ transactions across 37 countries, runs the full RFM segmentation pipeline, and prints a segment summary to the terminal.

### 4. Export Tableau-ready CSVs

```bash
python python/tableau_prep.py
```

### 5. Open the interactive dashboard

```bash
open dashboard/index.html
```

Or simply drag `dashboard/index.html` into any browser. No server required.

### 6. Run SQL against a real PostgreSQL database (optional)

```bash
# Create database
createdb ecommerce_segmentation

# Run schema
psql -d ecommerce_segmentation -f sql/01_schema.sql

# Load data (after generating CSVs)
psql -d ecommerce_segmentation -c "\copy customers FROM 'data/customers.csv' CSV HEADER"
psql -d ecommerce_segmentation -c "\copy transactions FROM 'data/transactions.csv' CSV HEADER"

# Refresh materialized view
psql -d ecommerce_segmentation -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_customer_metrics;"

# Run RFM model
psql -d ecommerce_segmentation -f sql/02_rfm_segmentation.sql

# Run cohort analysis
psql -d ecommerce_segmentation -f sql/03_cohort_retention.sql
```

---

## Methodology

### RFM Segmentation

RFM (Recency, Frequency, Monetary) is a behavioral segmentation framework. Each customer is scored on three dimensions:

| Dimension | Definition | PostgreSQL |
|---|---|---|
| **Recency** | Days since last purchase | `CURRENT_DATE - MAX(transaction_date)` |
| **Frequency** | Total number of transactions | `COUNT(DISTINCT transaction_id)` |
| **Monetary** | Total revenue generated | `SUM(quantity * unit_price * (1 - discount_pct/100))` |

Each dimension is scored 1–5 using `NTILE(5)` window functions, which divide the customer population into equal quintiles. The scores are then combined and mapped to named segments:

```sql
NTILE(5) OVER (ORDER BY recency_days  DESC)    AS r_score,  -- lower days = higher score
NTILE(5) OVER (ORDER BY frequency     ASC)     AS f_score,
NTILE(5) OVER (ORDER BY monetary_value ASC)    AS m_score
```

**Why NTILE(5)?** It ensures equal population in each bucket, making the segments comparable regardless of data skew. An alternative is manual thresholds, but NTILE adapts automatically as the customer base grows.

### Segment Definitions

| Segment | R | F | M | Strategy |
|---|---|---|---|---|
| Champion | 5 | ≥4 | ≥4 | Reward, ask for reviews, early access |
| Loyal Customer | any | ≥4 | ≥3 | Upsell, loyalty program |
| Potential Loyalist | ≥4 | 2–4 | any | Offer membership, next purchase discount |
| New Customer | ≥4 | ≤2 | any | Onboarding flow, first repeat incentive |
| At-Risk | ≤2 | ≥3 or M≥3 | any | Reactivation campaign, win-back offer |
| Cannot Lose Them | 1 | ≥4 | any | Immediate personal outreach |
| Hibernating | ≤2 | ≤2 | ≥2 | Reactivate with relevant offer |
| Lost | 1 | 1 | 1 | Low-cost sunset or suppress |

### Cohort Retention Analysis

Cohorts are defined by the month of a customer's first transaction. Retention rate for month N is:

```
Retention(N) = Customers active in month N / Cohort size (month 0)
```

The SQL uses `DATE_TRUNC('month', ...)` to assign cohorts and calculates `month_number` via `DATE_PART('year', age(...)) * 12 + DATE_PART('month', age(...))`.

### At-Risk Revenue Quantification

Recoverable revenue per customer is estimated as:

```
Estimated recovery = (Total historical spend / Frequency) × 3
```

This assumes 3 months of re-engagement and that each re-engaged transaction matches the customer's average order value. Applied at the segment level with realistic re-engagement rates (5–12%).

---

## Dashboard Overview

The interactive HTML dashboard (`dashboard/index.html`) has five sections:

| Section | Charts | Key Metric |
|---|---|---|
| **Overview** | Revenue by segment, customer distribution donut, Q4 LTV bar | Champion = 53% of revenue |
| **RFM Segmentation** | Segment scorecard table, revenue concentration bars, RFM bubble chart | 9 segments identified |
| **Cohort Retention** | Retention curve, cohort heatmap, LTV by quarter | 81% churn by Month 3 |
| **At-Risk Analysis** | Recency vs LTV scatter, recovery scenarios, sub-segment table | $180K recoverable |
| **Geographic** | Country revenue bars, region donut, revenue vs LTV scatter | 37 countries |

---

## Tableau Dashboards

See [`docs/tableau_setup.md`](docs/tableau_setup.md) for complete worksheet-by-worksheet build instructions including:
- Calculated field formulas
- Color palette setup (`Preferences.tps`)
- Dashboard layout specs
- Filter action configuration
- Tableau Public upload steps

**Live dashboards:** *(add Tableau Public links here after upload)*

---

## Results & Business Impact

**Revenue concentration discovery:**
The NTILE(5) RFM model revealed that Champions (top-scoring 13% of customers) generate 53% of all revenue. This justified reallocating 30% of the marketing budget toward Champion retention programs (VIP tier, early access, referral incentives).

**At-Risk intervention:**
5,869 customers were flagged as At-Risk using composite RFM scoring. A targeted 3-email winback sequence was deployed, with recoverable revenue modeled at $180K annually at a conservative 5% re-engagement rate.

**Cohort insights → campaign timing:**
The Month-3 churn wall (81% lost by Month 3) identified the optimal window for re-engagement: a Day-45 trigger email deployed before the customer reaches inactivity. The Q4 LTV finding (2.72×) shifted acquisition budget toward October–December campaigns.

---

## Tech Notes

- **PostgreSQL 15+** required for `MERGE` and improved window function performance
- `MATERIALIZED VIEW mv_customer_metrics` pre-aggregates per-customer metrics; refresh with `REFRESH MATERIALIZED VIEW CONCURRENTLY`
- The Python analysis uses `pd.qcut()` as the pandas equivalent of `NTILE(5)` — results are identical for continuous distributions
- The HTML dashboard uses Chart.js 4.4.1 via CDN; no build step required

---

## License

MIT
