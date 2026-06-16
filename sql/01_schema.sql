-- ============================================================
-- E-Commerce Customer Segmentation & Retention Analysis
-- 01_schema.sql  |  Database Schema Setup
-- ============================================================

-- ─── Extensions ───────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Tables ───────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS customers (
    customer_id     UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           TEXT        NOT NULL UNIQUE,
    country         VARCHAR(2)  NOT NULL,
    signup_date     DATE        NOT NULL,
    acquisition_channel VARCHAR(50),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    product_id      UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_name    TEXT        NOT NULL,
    category        VARCHAR(100),
    unit_price      NUMERIC(10,2) NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id     UUID        NOT NULL REFERENCES customers(customer_id),
    product_id      UUID        NOT NULL REFERENCES products(product_id),
    transaction_date DATE        NOT NULL,
    quantity        INTEGER     NOT NULL CHECK (quantity > 0),
    unit_price      NUMERIC(10,2) NOT NULL,
    discount_pct    NUMERIC(5,2) DEFAULT 0,
    country         VARCHAR(2),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Derived / Materialized Views ─────────────────────────

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_customer_metrics AS
SELECT
    c.customer_id,
    c.country,
    c.signup_date,
    c.acquisition_channel,
    COUNT(DISTINCT t.transaction_id)                                    AS frequency,
    MAX(t.transaction_date)                                             AS last_purchase_date,
    CURRENT_DATE - MAX(t.transaction_date)                             AS recency_days,
    SUM(t.quantity * t.unit_price * (1 - COALESCE(t.discount_pct,0)/100)) AS monetary_value,
    MIN(t.transaction_date)                                             AS first_purchase_date,
    COUNT(DISTINCT DATE_TRUNC('month', t.transaction_date))            AS active_months
FROM customers c
JOIN transactions t USING (customer_id)
GROUP BY c.customer_id, c.country, c.signup_date, c.acquisition_channel;

CREATE UNIQUE INDEX ON mv_customer_metrics (customer_id);

-- ─── Indexes ──────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_txn_customer   ON transactions (customer_id);
CREATE INDEX IF NOT EXISTS idx_txn_date       ON transactions (transaction_date);
CREATE INDEX IF NOT EXISTS idx_txn_country    ON transactions (country);
CREATE INDEX IF NOT EXISTS idx_cust_country   ON customers (country);
CREATE INDEX IF NOT EXISTS idx_cust_signup    ON customers (signup_date);
