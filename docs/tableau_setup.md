# Tableau Dashboard Setup Guide

Four Tableau Public dashboards replicate this analysis end-to-end.
All data sources are in `data/tableau_*.csv`.

---

## Data Sources

| CSV file | Primary use |
|---|---|
| `tableau_rfm_customers.csv` | RFM segment explorer, LTV analysis |
| `tableau_cohort_retention.csv` | Cohort heatmap, retention curves |
| `tableau_monthly_revenue.csv` | Revenue trend, category breakdown |
| `tableau_geo_summary.csv` | Geographic choropleth, country table |

---

## Dashboard 1 — RFM Segment Analysis

**Source:** `tableau_rfm_customers.csv`

### Worksheets to build

**Sheet 1: Segment Revenue Bar**
- Rows: `Segment`
- Columns: `SUM(Monetary Value)`
- Color: `Segment` (use custom palette matching dashboard colors)
- Sort: Descending by SUM(Monetary Value)
- Add reference line at overall average

**Sheet 2: Segment Customer Count**
- Rows: `Segment`
- Columns: `COUNTD(Customer Id)`
- Color: same as Sheet 1

**Sheet 3: RFM Scatter**
- Rows: `AVG(Recency Days)`
- Columns: `AVG(Frequency)`
- Size: `SUM(Monetary Value)`
- Color: `Segment`
- Tooltip: Customer count, Avg LTV, Avg Recency

**Sheet 4: KPI Summary**
- Use `SUM(Monetary Value)` filtered to Segment = "Champion"
- Show as single number: `$23.3M`
- Add annotation: "53% of total revenue"

### Calculated Fields

```
// LTV Tier
IF [Monetary Value] > 2000 THEN "High"
ELSEIF [Monetary Value] > 500 THEN "Mid"
ELSE "Low"
END

// Is Champion (already in CSV, but for reference)
IF [Segment] = "Champion" THEN 1 ELSE 0 END

// Revenue Share
SUM([Monetary Value]) / TOTAL(SUM([Monetary Value]))
```

### Dashboard Layout
- KPI row across top (4 metrics)
- Segment bar chart (left, 60% width)
- RFM scatter (right, 40% width)
- Filter action: click segment → highlight on scatter

---

## Dashboard 2 — Cohort Retention

**Source:** `tableau_cohort_retention.csv`

### Worksheets to build

**Sheet 5: Cohort Heatmap**
- Rows: `Cohort Month` (discrete, formatted as MMM YYYY)
- Columns: `Month Number` (discrete, 0–12)
- Color: `AVG(Retention Rate Pct)` — use orange-teal diverging palette
  - Min: 0% (orange), Mid: 15% (neutral), Max: 100% (teal)
- Text: `AVG(Retention Rate Pct)` formatted as `0.0%`
- Mark type: Square

**Sheet 6: Average Retention Curve**
- Rows: `AVG(Retention Rate Pct)`
- Columns: `Month Number`
- Add reference line at Month 3 (coral dashed)
- Dual axis: add `AVG(Churn Rate Pct)` on secondary axis

**Sheet 7: Quarter LTV Comparison**
- Source: `tableau_rfm_customers.csv`
- Rows: `AVG(Monetary Value)`
- Columns: `Acq Quarter`
- Add annotation: "2.72× higher in Q4"

### Calculated Fields

```
// Retention label color
IF AVG([Retention Rate Pct]) > 25 THEN "High"
ELSEIF AVG([Retention Rate Pct]) > 15 THEN "Mid"
ELSE "Low"
END

// Month 3 flag
IF [Month Number] = 3 THEN "Critical Window" ELSE "" END
```

### Dashboard Layout
- Heatmap full width (top 55%)
- Retention curve (bottom left 60%)
- Quarter LTV bar (bottom right 40%)
- Filter: Cohort Year selector

---

## Dashboard 3 — At-Risk Recovery

**Source:** `tableau_rfm_customers.csv` (filtered to At-Risk)

### Worksheets to build

**Sheet 8: At-Risk vs Champion Comparison**
- Filter: `Segment IN ("At-Risk","Champion","Loyal Customer")`
- Scatter: Recency Days (x) vs Monetary Value (y)
- Color: Segment
- Size: Customer count

**Sheet 9: Recovery Scenarios**
- Manual data: create inline table
  - 5% → $176,210
  - 8% → $281,936
  - 12% → $422,904
- Bar chart with color by scenario

**Sheet 10: At-Risk Sub-segments**
- Filter: Segment = "At-Risk"
- Group by: Monetary Value (bins of $200)
- Show count and avg recency

### Dashboard Layout
- Header KPIs: 5,869 customers | $3.52M historical spend | $180K recoverable
- Left: At-Risk scatter vs other segments
- Right: Recovery scenario bars
- Bottom: Sub-segment table

---

## Dashboard 4 — Geographic Performance

**Source:** `tableau_geo_summary.csv`

### Worksheets to build

**Sheet 11: Choropleth Map**
- Mark type: Map
- Color: `SUM(Total Revenue)` — sequential blue
- Geographic role: `Country Name` → Country/Region
- Tooltip: Country, Revenue, Customers, Avg LTV

**Sheet 12: Country Revenue Bars**
- Rows: `Country Name` (top 15 by revenue)
- Columns: `SUM(Total Revenue)`
- Color: `Region`

**Sheet 13: Revenue vs LTV Scatter**
- Rows: `AVG(Avg Ltv)`
- Columns: `SUM(Total Revenue)`
- Size: `SUM(Customers)`
- Color: `Region`
- Label: `Country` for top 10 by revenue

### Dashboard Layout
- Map full width (top 50%)
- Country bars (bottom left 55%)
- Revenue/LTV scatter (bottom right 45%)
- Region filter (top right corner)

---

## Tableau Public Upload Steps

1. Complete all 4 dashboards in Tableau Desktop
2. `Server → Tableau Public → Save to Tableau Public As…`
3. Set all dashboards to public
4. Copy the embed URL for each dashboard
5. Add links to `README.md` under "Live Dashboards"

---

## Custom Color Palette

Add to your Tableau `Preferences.tps` file:

```xml
<color-palette name="RFM Segments" type="regular">
  <color>#7c6edb</color>
  <color>#3ecf8e</color>
  <color>#f0724e</color>
  <color>#4d9ef0</color>
  <color>#f0b429</color>
  <color>#d45fb5</color>
  <color>#5a5f78</color>
  <color>#3ecf8e</color>
  <color>#8b90a8</color>
</color-palette>
```

Preferences file locations:
- **Mac:** `~/Documents/My Tableau Repository/Preferences.tps`
- **Windows:** `C:\Users\[user]\Documents\My Tableau Repository\Preferences.tps`
