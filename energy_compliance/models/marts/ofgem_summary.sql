{{ config(materialized='table') }}

-- Ofgem Social Obligations Reporting: quarterly summary
-- Ref: https://www.ofgem.gov.uk/data/debt-and-arrears-indicators

WITH stg_accounts AS (
    SELECT * FROM {{ ref('stg_accounts') }}
),

stg_arrangements AS (
    SELECT account_id
    FROM {{ ref('stg_debt_arrangements') }}
    WHERE recency_rank = 1
)

SELECT
    ROUND(AVG(
        CASE WHEN sa.has_debt AND arr.account_id IS NULL
             THEN sa.debt_amount_gbp END
    )::NUMERIC, 2)                                                      AS avg_debt_no_arrangement_gbp,

    ROUND(AVG(
        CASE WHEN arr.account_id IS NOT NULL
             THEN sa.debt_amount_gbp END
    )::NUMERIC, 2)                                                      AS avg_debt_with_arrangement_gbp,

    ROUND(
        100.0 * COUNT(CASE WHEN sa.is_ppm_in_debt THEN 1 END)
        / NULLIF(COUNT(CASE WHEN sa.has_debt THEN 1 END), 0)
    , 1)                                                                AS pct_repaying_via_ppm,

    COUNT(CASE WHEN sa.has_debt THEN 1 END)                            AS accounts_with_debt,
    COUNT(CASE WHEN sa.has_debt AND arr.account_id IS NULL THEN 1 END) AS accounts_no_arrangement,

    ROUND(SUM(
        CASE WHEN sa.is_over_91_days THEN sa.debt_amount_gbp ELSE 0 END
    )::NUMERIC, 2)                                                      AS total_debt_over_91_days_gbp,

    DATE_TRUNC('quarter', CURRENT_DATE)::DATE                          AS reporting_quarter,
    CURRENT_DATE                                                        AS report_date

FROM stg_accounts sa
LEFT JOIN stg_arrangements arr ON sa.account_id = arr.account_id
