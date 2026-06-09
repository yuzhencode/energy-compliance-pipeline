-- =============================================================================
-- Mart layer: ofgem_summary
-- =============================================================================
-- Layer:   Mart
-- Source:  staging views (stg_accounts, stg_debt_arrangements)
-- Purpose: Quarterly Ofgem Social Obligations Reporting — summary metrics.
--
-- Indicators covered (mapped directly to Ofgem published timetable):
--   1. Average debt level — no repayment arrangement (arrears)
--   2. Average debt level — with active repayment arrangement
--   3. Proportion of in-debt customers repaying via PPM (%)
--   4. Total accounts with energy debt (count)
--   5. Accounts in arrears with no arrangement (count)
--   6. Total financial value of debt existing >91 days (£)
--
-- Ref: Ofgem Indicators Timetable Jan–Mar 2026
--      https://www.ofgem.gov.uk/sites/default/files/2026-01/Ofgem%20indicators%20publication%20timetable%20January%20to%20March%202026.pdf
-- Ref: Ofgem Debt & Arrears Indicators data portal
--      https://www.ofgem.gov.uk/data/debt-and-arrears-indicators
-- =============================================================================

WITH stg_accounts AS (
    SELECT
        account_id,
        fuel_type,
        payment_method,
        debt_amount_gbp,
        debt_age_days,
        has_debt,
        is_over_91_days,
        is_ppm_in_debt
    FROM (
        SELECT
            account_id,
            LOWER(fuel_type)                                        AS fuel_type,
            LOWER(payment_method)                                   AS payment_method,
            COALESCE(debt_amount, 0)                                AS debt_amount_gbp,
            COALESCE(debt_age_days, 0)                              AS debt_age_days,
            CASE WHEN debt_amount  > 0   THEN TRUE ELSE FALSE END   AS has_debt,
            CASE WHEN debt_age_days > 91 THEN TRUE ELSE FALSE END   AS is_over_91_days,
            CASE WHEN payment_method = 'prepayment_meter'
                  AND debt_amount > 0   THEN TRUE ELSE FALSE END    AS is_ppm_in_debt
        FROM accounts
        WHERE account_status != 'closed'
    ) a
),

stg_arrangements AS (
    SELECT account_id
    FROM (
        SELECT
            account_id,
            ROW_NUMBER() OVER (
                PARTITION BY account_id
                ORDER BY arrangement_date DESC
            ) AS recency_rank
        FROM debt_repayment_arrangements
        WHERE status = 'active'
    ) ranked
    WHERE recency_rank = 1
)

SELECT
    -- Indicator 1: avg arrears, no arrangement
    ROUND(AVG(
        CASE WHEN sa.has_debt AND arr.account_id IS NULL
             THEN sa.debt_amount_gbp END
    ), 2)                                                               AS avg_debt_no_arrangement_gbp,

    -- Indicator 2: avg debt with arrangement
    ROUND(AVG(
        CASE WHEN arr.account_id IS NOT NULL
             THEN sa.debt_amount_gbp END
    ), 2)                                                               AS avg_debt_with_arrangement_gbp,

    -- Indicator 3: proportion repaying via PPM (%)
    ROUND(
        100.0 * COUNT(CASE WHEN sa.is_ppm_in_debt THEN 1 END)
        / NULLIF(COUNT(CASE WHEN sa.has_debt THEN 1 END), 0)
    , 1)                                                                AS pct_repaying_via_ppm,

    -- Indicator 4: total accounts with energy debt
    COUNT(CASE WHEN sa.has_debt THEN 1 END)                            AS accounts_with_debt,

    -- Indicator 5: accounts in arrears, no arrangement
    COUNT(CASE WHEN sa.has_debt AND arr.account_id IS NULL THEN 1 END) AS accounts_no_arrangement,

    -- Indicator 6: total debt value >91 days
    ROUND(SUM(
        CASE WHEN sa.is_over_91_days THEN sa.debt_amount_gbp ELSE 0 END
    ), 2)                                                               AS total_debt_over_91_days_gbp,

    DATE_TRUNC('quarter', CURRENT_DATE)::DATE                          AS reporting_quarter,
    CURRENT_DATE                                                        AS report_date

FROM stg_accounts sa
LEFT JOIN stg_arrangements arr ON sa.account_id = arr.account_id;
