"""
tableau_prep.py
===============
Prepares and exports clean data extracts optimized for Tableau Desktop.
Run this after generate_data.py — assumes CSVs exist in data/

Outputs four Tableau-ready CSVs:
    data/tableau_rfm_customers.csv      — one row per customer with all RFM fields
    data/tableau_cohort_retention.csv   — long-format cohort × month retention
    data/tableau_monthly_revenue.csv    — monthly revenue time series
    data/tableau_geo_summary.csv        — country-level aggregates
"""

import pandas as pd
import numpy as np
from datetime import date, timedelta

print("Loading source data...")
customers = pd.read_csv("data/customers.csv", parse_dates=["signup_date"])
txn       = pd.read_csv("data/transactions.csv", parse_dates=["transaction_date"])
rfm       = pd.read_csv("data/rfm_scores.csv")
coh_mat   = pd.read_csv("data/cohort_matrix.csv")

# ── 1. RFM customers flat export ──────────────────────────────
print("Preparing RFM export...")
rfm_tableau = rfm[[
    "customer_id","country","acquisition_channel",
    "recency_days","frequency","monetary_value",
    "r_score","f_score","m_score","rfm_total","segment","acq_quarter"
]].copy()

# Segment order for Tableau sorting
seg_order = {
    "Champion":1,"Loyal Customer":2,"Potential Loyalist":3,
    "New Customer":4,"Promising":5,"Need Attention":6,
    "At-Risk":7,"Hibernating":8,"Cannot Lose Them":9,"Lost":10
}
rfm_tableau["segment_rank"] = rfm_tableau["segment"].map(seg_order).fillna(10)
rfm_tableau["is_champion"]  = (rfm_tableau["segment"] == "Champion").astype(int)
rfm_tableau["is_at_risk"]   = (rfm_tableau["segment"] == "At-Risk").astype(int)

rfm_tableau.to_csv("data/tableau_rfm_customers.csv", index=False)
print(f"  → {len(rfm_tableau):,} rows")

# ── 2. Cohort retention (long format) ────────────────────────
print("Preparing cohort retention export...")
month_cols = [str(i) for i in range(13)]
retention_long = coh_mat.melt(
    id_vars=["cohort_month"],
    value_vars=[c for c in month_cols if c in coh_mat.columns],
    var_name="month_number",
    value_name="retention_rate_pct"
)
retention_long["month_number"] = retention_long["month_number"].astype(int)
retention_long["churn_rate_pct"] = 100 - retention_long["retention_rate_pct"]
retention_long = retention_long.dropna(subset=["retention_rate_pct"])

# Add cohort year/quarter for filtering
retention_long["cohort_month_dt"] = pd.to_datetime(retention_long["cohort_month"])
retention_long["cohort_year"]     = retention_long["cohort_month_dt"].dt.year
retention_long["cohort_quarter"]  = retention_long["cohort_month_dt"].dt.quarter

retention_long.to_csv("data/tableau_cohort_retention.csv", index=False)
print(f"  → {len(retention_long):,} rows")

# ── 3. Monthly revenue time series ───────────────────────────
print("Preparing monthly revenue export...")
txn["revenue"]        = txn["unit_price"] * txn["quantity"] * (1 - txn["discount_pct"].fillna(0)/100)
txn["month"]          = txn["transaction_date"].dt.to_period("M").astype(str)
txn["year"]           = txn["transaction_date"].dt.year
txn["quarter"]        = txn["transaction_date"].dt.quarter

monthly = (
    txn.groupby(["month","year","quarter","category"])
    .agg(
        transactions = ("transaction_id", "count"),
        customers    = ("customer_id",    "nunique"),
        revenue      = ("revenue",        "sum"),
        avg_order    = ("revenue",        "mean"),
    )
    .reset_index()
    .round(2)
)
monthly.to_csv("data/tableau_monthly_revenue.csv", index=False)
print(f"  → {len(monthly):,} rows")

# ── 4. Geographic summary ─────────────────────────────────────
print("Preparing geographic export...")
country_names = {
    "US":"United States","GB":"United Kingdom","DE":"Germany","FR":"France",
    "CA":"Canada","JP":"Japan","AU":"Australia","BR":"Brazil","IN":"India",
    "MX":"Mexico","IT":"Italy","ES":"Spain","NL":"Netherlands","SE":"Sweden",
    "NO":"Norway","DK":"Denmark","CH":"Switzerland","PL":"Poland","PT":"Portugal",
    "BE":"Belgium","AT":"Austria","SG":"Singapore","NZ":"New Zealand",
    "ZA":"South Africa","AE":"United Arab Emirates","TH":"Thailand",
    "MY":"Malaysia","PH":"Philippines","ID":"Indonesia","KR":"South Korea",
    "TW":"Taiwan","HK":"Hong Kong","AR":"Argentina","CL":"Chile",
    "CO":"Colombia","NG":"Nigeria","EG":"Egypt",
}
region_map = {
    "US":"Americas","CA":"Americas","MX":"Americas","BR":"Americas",
    "AR":"Americas","CL":"Americas","CO":"Americas",
    "GB":"Europe","DE":"Europe","FR":"Europe","IT":"Europe","ES":"Europe",
    "NL":"Europe","SE":"Europe","NO":"Europe","DK":"Europe","CH":"Europe",
    "PL":"Europe","PT":"Europe","BE":"Europe","AT":"Europe",
    "JP":"APAC","AU":"APAC","IN":"APAC","SG":"APAC","NZ":"APAC",
    "TH":"APAC","MY":"APAC","PH":"APAC","ID":"APAC","KR":"APAC",
    "TW":"APAC","HK":"APAC",
    "AE":"Middle East","ZA":"Africa","NG":"Africa","EG":"Africa",
}

geo = (
    rfm.groupby("country")
    .agg(
        customers      = ("customer_id",    "count"),
        total_revenue  = ("monetary_value", "sum"),
        avg_ltv        = ("monetary_value", "mean"),
        avg_recency    = ("recency_days",   "mean"),
        avg_frequency  = ("frequency",      "mean"),
        champion_count = ("is_champion",    "sum") if "is_champion" in rfm.columns else ("customer_id", "count"),
    )
    .reset_index()
    .round(2)
)
geo["country_name"] = geo["country"].map(country_names).fillna(geo["country"])
geo["region"]       = geo["country"].map(region_map).fillna("Other")
geo["pct_revenue"]  = (geo["total_revenue"] / geo["total_revenue"].sum() * 100).round(2)
geo["pct_customers"]= (geo["customers"] / geo["customers"].sum() * 100).round(2)
geo = geo.sort_values("total_revenue", ascending=False)
geo.to_csv("data/tableau_geo_summary.csv", index=False)
print(f"  → {len(geo):,} rows (countries)")

print("\nAll Tableau extracts saved. ✓")
print("\nImport order into Tableau:")
print("  1. tableau_rfm_customers.csv    → RFM Analysis, Segment dashboards")
print("  2. tableau_cohort_retention.csv → Cohort Retention dashboard")
print("  3. tableau_monthly_revenue.csv  → Revenue Trends dashboard")
print("  4. tableau_geo_summary.csv      → Geographic Performance dashboard")
