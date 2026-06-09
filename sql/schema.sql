-- =============================================================================
-- energy-compliance-pipeline: raw layer schema
-- =============================================================================
-- Layer:   Raw
-- Purpose: Source-faithful tables. No business logic applied here.
--          Staging layer (sql/staging/) handles normalisation.
-- Ref:     Ofgem Social Obligations Reporting (Quarterly)
--          https://www.ofgem.gov.uk/data/debt-and-arrears-indicators
-- =============================================================================

CREATE TABLE IF NOT EXISTS accounts (
    account_id          VARCHAR(20)     PRIMARY KEY,
    customer_name       VARCHAR(100)    NOT NULL,
    postcode            VARCHAR(10),
    fuel_type           VARCHAR(10)     CHECK (fuel_type IN ('gas', 'electric', 'dual')),
    payment_method      VARCHAR(20)     CHECK (payment_method IN ('direct_debit', 'prepayment_meter', 'cash', 'other')),
    debt_amount         NUMERIC(10,2)   DEFAULT 0,
    debt_age_days       INTEGER         DEFAULT 0,
    account_status      VARCHAR(20)     CHECK (account_status IN ('active', 'closed', 'disputed')),
    created_at          TIMESTAMP       DEFAULT NOW(),
    updated_at          TIMESTAMP       DEFAULT NOW()
);

-- Tracks formal repayment arrangements between supplier and customer.
-- Ofgem indicator: "Average level of debt remaining where there is an arrangement to repay"
-- Ref: Ofgem Indicators Timetable Jan-Mar 2026
--      https://www.ofgem.gov.uk/sites/default/files/2026-01/Ofgem%20indicators%20publication%20timetable%20January%20to%20March%202026.pdf
CREATE TABLE IF NOT EXISTS debt_repayment_arrangements (
    arrangement_id      SERIAL          PRIMARY KEY,
    account_id          VARCHAR(20)     NOT NULL REFERENCES accounts(account_id),
    arrangement_date    DATE            NOT NULL,
    weekly_rate_gbp     NUMERIC(8,2),   -- Ofgem indicator: average weekly debt repayment rate (£)
    plan_weeks          INTEGER,        -- Ofgem indicator: average length of repayment plan (weeks)
    status              VARCHAR(20)     CHECK (status IN ('active', 'completed', 'broken')),
    created_at          TIMESTAMP       DEFAULT NOW()
);

-- Tracks remote switch events (prepayment meter installations for debt recovery).
-- Ofgem indicator: "Number of disconnections for non-payment of debt"
-- Ref: Ofgem Social Obligations Reporting (Quarterly)
CREATE TABLE IF NOT EXISTS remote_switch_events (
    event_id            SERIAL          PRIMARY KEY,
    account_id          VARCHAR(20)     NOT NULL REFERENCES accounts(account_id),
    switch_type         VARCHAR(20)     CHECK (switch_type IN ('prepayment', 'credit', 'emergency')),
    switch_date         DATE            NOT NULL,
    actioned_by         VARCHAR(50),
    outcome             VARCHAR(20)     CHECK (outcome IN ('success', 'failed', 'pending')),
    created_at          TIMESTAMP       DEFAULT NOW()
);

-- Audit trail for every pipeline run.
CREATE TABLE IF NOT EXISTS report_runs (
    run_id              SERIAL          PRIMARY KEY,
    report_week         DATE            NOT NULL,
    generated_at        TIMESTAMP       DEFAULT NOW(),
    row_count           INTEGER,
    validation_passed   BOOLEAN,
    output_path         TEXT
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_accounts_status       ON accounts(account_status);
CREATE INDEX IF NOT EXISTS idx_accounts_fuel         ON accounts(fuel_type);
CREATE INDEX IF NOT EXISTS idx_arrangements_account  ON debt_repayment_arrangements(account_id);
CREATE INDEX IF NOT EXISTS idx_arrangements_status   ON debt_repayment_arrangements(status);
CREATE INDEX IF NOT EXISTS idx_switch_account        ON remote_switch_events(account_id);
CREATE INDEX IF NOT EXISTS idx_switch_date           ON remote_switch_events(switch_date);
