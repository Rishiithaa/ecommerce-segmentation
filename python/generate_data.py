"""
generate_data.py
================
Generates a realistic synthetic e-commerce dataset of 300,000+ transactions
across 37 countries, then runs the full RFM + Cohort analysis pipeline in pandas.

Outputs:
    data/transactions.csv
    data/customers.csv
    data/rfm_scores.csv
    data/cohort_matrix.csv
    data/segment_summary.csv
"""

import os
import sys
import numpy as np
import pandas as pd
from datetime import date, timedelta
import random
import uuid
import warnings

warnings.filterwarnings("ignore")
np.random.seed(42)
random.seed(42)

# Print UTF-8 cleanly even on consoles that default to a legacy codec (e.g.
# Windows cp1252), so the script never dies on a stray arrow or check mark.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Resolve paths relative to the repo root, not the caller's cwd, and make sure
# the output directory exists so a fresh clone runs without manual setup.
ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ─── Config ───────────────────────────────────────────────
N_CUSTOMERS   = 45_000
START_DATE    = date(2021, 1, 1)
END_DATE      = date(2023, 12, 31)
DATE_RANGE    = (END_DATE - START_DATE).days

COUNTRIES = [
    ("US","United States",0.28), ("GB","United Kingdom",0.10), ("DE","Germany",0.07),
    ("FR","France",0.06),        ("CA","Canada",0.05),         ("AU","Australia",0.04),
    ("JP","Japan",0.04),         ("BR","Brazil",0.03),         ("IN","India",0.03),
    ("MX","Mexico",0.02),        ("IT","Italy",0.02),          ("ES","Spain",0.02),
    ("NL","Netherlands",0.02),   ("SE","Sweden",0.01),         ("NO","Norway",0.01),
    ("DK","Denmark",0.01),       ("CH","Switzerland",0.01),    ("PL","Poland",0.01),
    ("PT","Portugal",0.01),      ("BE","Belgium",0.01),        ("AT","Austria",0.005),
    ("SG","Singapore",0.005),    ("NZ","New Zealand",0.005),   ("ZA","South Africa",0.005),
    ("AE","United Arab Emirates",0.005), ("TH","Thailand",0.005), ("MY","Malaysia",0.005),
    ("PH","Philippines",0.005),  ("ID","Indonesia",0.005),     ("KR","South Korea",0.005),
    ("TW","Taiwan",0.004),       ("HK","Hong Kong",0.004),     ("AR","Argentina",0.003),
    ("CL","Chile",0.003),        ("CO","Colombia",0.003),      ("NG","Nigeria",0.002),
    ("EG","Egypt",0.002),
]

CHANNELS = ["organic_search","paid_search","social","email","referral","direct","affiliate"]
CHANNEL_WEIGHTS = [0.30, 0.20, 0.18, 0.12, 0.10, 0.07, 0.03]

CATEGORIES = {
    "Electronics":   (120, 800),
    "Clothing":      (25,  150),
    "Home & Garden": (30,  300),
    "Books":         (8,   40),
    "Sports":        (20,  200),
    "Beauty":        (15,  100),
    "Toys":          (10,  80),
    "Food & Drink":  (5,   50),
}

# ─── Generate Customers ───────────────────────────────────
print("Generating customers...")
country_codes = [c[0] for c in COUNTRIES]
country_weights = [c[2] for c in COUNTRIES]
country_weights = np.array(country_weights) / sum(country_weights)

signup_offsets = np.random.randint(0, DATE_RANGE - 30, N_CUSTOMERS)
signup_dates   = [START_DATE + timedelta(days=int(d)) for d in signup_offsets]

customers_df = pd.DataFrame({
    "customer_id":          [str(uuid.uuid4()) for _ in range(N_CUSTOMERS)],
    "country":              np.random.choice(country_codes, N_CUSTOMERS, p=country_weights),
    "signup_date":          signup_dates,
    "acquisition_channel":  np.random.choice(CHANNELS, N_CUSTOMERS, p=CHANNEL_WEIGHTS),
})

# ─── Generate Transactions ────────────────────────────────
print("Generating transactions...")

# Champions (~8%) buy frequently near end of period; others distributed
champion_mask = np.random.random(N_CUSTOMERS) < 0.08
customer_txn_counts = np.where(
    champion_mask,
    np.random.randint(20, 60, N_CUSTOMERS),   # Champions
    np.random.negative_binomial(2, 0.4, N_CUSTOMERS) + 1  # Everyone else
)
customer_txn_counts = np.clip(customer_txn_counts, 1, 80)

rows = []
for i, row in customers_df.iterrows():
    n_txns = customer_txn_counts[i]
    cid    = row["customer_id"]
    signup = (row["signup_date"] - START_DATE).days

    for _ in range(n_txns):
        cat   = random.choice(list(CATEGORIES.keys()))
        lo, hi = CATEGORIES[cat]

        # Champions: cluster purchases toward recent months
        if champion_mask[i]:
            day_offset = signup + np.random.randint(
                max(0, DATE_RANGE - 180), DATE_RANGE
            )
        else:
            day_offset = signup + np.random.randint(0, max(1, DATE_RANGE - signup))

        day_offset = min(day_offset, DATE_RANGE)
        txn_date   = START_DATE + timedelta(days=int(day_offset))

        rows.append({
            "transaction_id":   str(uuid.uuid4()),
            "customer_id":      cid,
            "transaction_date": txn_date,
            "category":         cat,
            "unit_price":       round(random.uniform(lo, hi), 2),
            "quantity":         np.random.choice([1,1,1,2,2,3], p=[0.5,0.2,0.1,0.1,0.07,0.03]),
            "discount_pct":     np.random.choice([0,5,10,15,20], p=[0.60,0.15,0.13,0.07,0.05]),
            "country":          row["country"],
        })

txn_df = pd.DataFrame(rows)
txn_df["revenue"] = txn_df["unit_price"] * txn_df["quantity"] * (1 - txn_df["discount_pct"] / 100)
print(f"  → {len(txn_df):,} transactions across {txn_df['country'].nunique()} countries")

# ─── RFM Analysis ─────────────────────────────────────────
print("Running RFM segmentation...")
SNAPSHOT = END_DATE + timedelta(days=1)

rfm = (
    txn_df.groupby("customer_id")
    .agg(
        last_purchase  = ("transaction_date", "max"),
        frequency      = ("transaction_id",   "count"),
        monetary_value = ("revenue",          "sum"),
    )
    .reset_index()
)
rfm["recency_days"] = (pd.Timestamp(SNAPSHOT) - pd.to_datetime(rfm["last_purchase"])).dt.days

# NTILE(5) via pandas qcut
rfm["r_score"] = pd.qcut(rfm["recency_days"],  5, labels=[5,4,3,2,1]).astype(int)
rfm["f_score"] = pd.qcut(rfm["frequency"],     5, labels=[1,2,3,4,5], duplicates="drop").astype(int)
rfm["m_score"] = pd.qcut(rfm["monetary_value"],5, labels=[1,2,3,4,5], duplicates="drop").astype(int)
rfm["rfm_total"] = rfm["r_score"] + rfm["f_score"] + rfm["m_score"]

def assign_segment(row):
    r, f, m = row["r_score"], row["f_score"], row["m_score"]
    if r == 5 and f >= 4 and m >= 4:              return "Champion"
    if f >= 4 and m >= 3:                         return "Loyal Customer"
    if r >= 4 and 2 <= f <= 4:                    return "Potential Loyalist"
    if r >= 4 and f <= 2:                         return "New Customer"
    if r == 3 and f <= 2:                         return "Promising"
    if r == 3 and f == 3 and m == 3:              return "Need Attention"
    if r <= 2 and (f >= 3 or m >= 3):             return "At-Risk"
    if r == 1 and f >= 4:                         return "Cannot Lose Them"
    if r <= 2 and f <= 2 and m >= 2:              return "Hibernating"
    return "Lost"

rfm["segment"] = rfm.apply(assign_segment, axis=1)
rfm = rfm.merge(customers_df[["customer_id","country","acquisition_channel"]], on="customer_id")

print("\n=== RFM Segment Summary ===")
seg_summary = (
    rfm.groupby("segment")
    .agg(
        customers      = ("customer_id", "count"),
        total_revenue  = ("monetary_value", "sum"),
        avg_ltv        = ("monetary_value", "mean"),
        avg_recency    = ("recency_days", "mean"),
        avg_frequency  = ("frequency", "mean"),
    )
    .round(2)
    .reset_index()
)
seg_summary["pct_customers"] = (seg_summary["customers"] / seg_summary["customers"].sum() * 100).round(2)
seg_summary["pct_revenue"]   = (seg_summary["total_revenue"] / seg_summary["total_revenue"].sum() * 100).round(2)
seg_summary = seg_summary.sort_values("total_revenue", ascending=False)
print(seg_summary[["segment","customers","pct_customers","total_revenue","pct_revenue","avg_ltv"]].to_string(index=False))

# At-Risk summary
at_risk = rfm[rfm["segment"] == "At-Risk"]
print(f"\nAt-Risk: {len(at_risk):,} customers | ${at_risk['monetary_value'].sum():,.0f} in historical spend")

# ─── Cohort Retention Analysis ────────────────────────────
print("\nRunning cohort retention analysis...")
txn_df["transaction_date"] = pd.to_datetime(txn_df["transaction_date"])

cohorts = (
    txn_df.groupby("customer_id")["transaction_date"]
    .min()
    .dt.to_period("M")
    .rename("cohort_month")
    .reset_index()
)

txn_with_cohort = txn_df.merge(cohorts, on="customer_id")
txn_with_cohort["activity_month"] = txn_with_cohort["transaction_date"].dt.to_period("M")
txn_with_cohort["month_number"]   = (
    txn_with_cohort["activity_month"].astype(int)
    - txn_with_cohort["cohort_month"].astype(int)
)

cohort_pivot = (
    txn_with_cohort[txn_with_cohort["month_number"] <= 12]
    .groupby(["cohort_month", "month_number"])["customer_id"]
    .nunique()
    .reset_index()
    .pivot(index="cohort_month", columns="month_number", values="customer_id")
)

cohort_sizes   = cohort_pivot[0]
retention_matrix = cohort_pivot.divide(cohort_sizes, axis=0).round(4) * 100

print("\n=== Retention Rate (%) by Month ===")
print(retention_matrix.iloc[:6, :7].to_string())

# Month 3 churn
m3_retention = retention_matrix[3].mean()
print(f"\nAvg Month-3 retention: {m3_retention:.1f}%  |  churn: {100-m3_retention:.1f}%")

# Q4 vs Q1 LTV
rfm["cohort_month"] = cohorts.set_index("customer_id")["cohort_month"].reindex(rfm["customer_id"]).values
rfm["cohort_month_ts"] = rfm["cohort_month"].apply(lambda x: x.to_timestamp() if pd.notna(x) else pd.NaT)
rfm["acq_quarter"] = rfm["cohort_month_ts"].dt.quarter

q_ltv = rfm.groupby("acq_quarter")["monetary_value"].mean().round(2)
print(f"\nLTV by acquisition quarter:\n{q_ltv}")
if 1 in q_ltv and 4 in q_ltv:
    print(f"\nQ4 / Q1 LTV ratio: {q_ltv[4] / q_ltv[1]:.2f}x")

# ─── Save outputs ─────────────────────────────────────────
print("\nSaving CSVs...")
customers_df.to_csv(os.path.join(DATA_DIR, "customers.csv"), index=False)
txn_df.to_csv(os.path.join(DATA_DIR, "transactions.csv"), index=False)
rfm.to_csv(os.path.join(DATA_DIR, "rfm_scores.csv"), index=False)
seg_summary.to_csv(os.path.join(DATA_DIR, "segment_summary.csv"), index=False)
retention_matrix.to_csv(os.path.join(DATA_DIR, "cohort_matrix.csv"))
print("Done.")
