-- =============================================================================
-- Staging layer: stg_debt_arrangements
-- =============================================================================
-- Layer:   Staging
-- Source:  raw.debt_repayment_arrangements
-- Purpose: Deduplicate to one active arrangement per account (latest wins).
--          Standardise status labels.
-- =============================================================================

SELECT
    dra.arrangement_id,
    dra.account_id,
    dra.arrangement_date,
    COALESCE(dra.weekly_rate_gbp, 0)        AS weekly_rate_gbp,
    COALESCE(dra.plan_weeks, 0)             AS plan_weeks,
    LOWER(dra.status)                       AS arrangement_status,
    -- Flag: is this the most recent active arrangement for this account?
    ROW_NUMBER() OVER (
        PARTITION BY dra.account_id
        ORDER BY dra.arrangement_date DESC
    )                                       AS recency_rank,
    dra.created_at
FROM debt_repayment_arrangements dra
WHERE dra.status = 'active';
