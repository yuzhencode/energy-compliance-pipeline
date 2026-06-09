-- =============================================================================
-- Mart layer: account_detail
-- =============================================================================
-- Layer:   Mart
-- Source:  staging (stg_accounts, stg_debt_arrangements, remote_switch_events)
-- Purpose: Account-level detail for Ofgem submission.
--          One row per active account with debt.
-- =============================================================================

WITH stg_accounts AS (
    SELECT
        account_id,
        UPPER(TRIM(customer_name))                          AS customer_name,
        UPPER(REPLACE(TRIM(postcode), ' ', ''))             AS postcode,
        LOWER(fuel_type)                                    AS fuel_type,
        LOWER(payment_method)                               AS payment_method,
        COALESCE(debt_amount, 0)                            AS debt_amount_gbp,
        COALESCE(debt_age_days, 0)                          AS debt_age_days,
        LOWER(account_status)                               AS account_status,
        CASE WHEN debt_age_days > 91 THEN TRUE ELSE FALSE END AS is_over_91_days
    FROM accounts
    WHERE account_status != 'closed'
      AND debt_amount > 0
),

latest_arrangement AS (
    SELECT account_id, weekly_rate_gbp, plan_weeks, status, arrangement_date
    FROM (
        SELECT
            account_id, weekly_rate_gbp, plan_weeks, status, arrangement_date,
            ROW_NUMBER() OVER (
                PARTITION BY account_id ORDER BY arrangement_date DESC
            ) AS rn
        FROM debt_repayment_arrangements
        WHERE status = 'active'
    ) ranked
    WHERE rn = 1
),

latest_switch AS (
    SELECT account_id, switch_type, switch_date, outcome
    FROM (
        SELECT
            account_id, switch_type, switch_date, outcome,
            ROW_NUMBER() OVER (
                PARTITION BY account_id ORDER BY switch_date DESC
            ) AS rn
        FROM remote_switch_events
    ) ranked
    WHERE rn = 1
)

SELECT
    sa.account_id,
    sa.customer_name,
    sa.postcode,
    sa.fuel_type,
    sa.payment_method,
    sa.debt_amount_gbp,
    sa.debt_age_days,
    sa.is_over_91_days,
    sa.account_status,
    -- Arrangement fields
    la.arrangement_date                                     AS arrangement_date,
    la.weekly_rate_gbp                                      AS arrangement_weekly_rate_gbp,
    la.plan_weeks                                           AS arrangement_plan_weeks,
    CASE WHEN la.account_id IS NOT NULL
         THEN TRUE ELSE FALSE END                           AS has_active_arrangement,
    -- Latest remote switch
    ls.switch_type                                          AS last_switch_type,
    ls.switch_date                                          AS last_switch_date,
    ls.outcome                                              AS last_switch_outcome,
    CURRENT_DATE                                            AS report_date
FROM stg_accounts sa
LEFT JOIN latest_arrangement la ON sa.account_id = la.account_id
LEFT JOIN latest_switch      ls ON sa.account_id = ls.account_id
ORDER BY sa.debt_amount_gbp DESC;
