{{ config(materialized='table') }}

WITH stg_accounts AS (
    SELECT * FROM {{ ref('stg_accounts') }}
    WHERE has_debt = TRUE
),

latest_arrangement AS (
    SELECT account_id, weekly_rate_gbp, plan_weeks, arrangement_date
    FROM {{ ref('stg_debt_arrangements') }}
    WHERE recency_rank = 1
),

latest_switch AS (
    SELECT DISTINCT ON (account_id)
        account_id, switch_type, switch_date, outcome
    FROM {{ source('raw', 'remote_switch_events') }}
    ORDER BY account_id, switch_date DESC
)

SELECT
    sa.account_id,
    sa.customer_name,
    sa.postcode_normalised                              AS postcode,
    sa.fuel_type,
    sa.payment_method,
    sa.debt_amount_gbp,
    sa.debt_age_days,
    sa.is_over_91_days,
    sa.account_status,
    la.arrangement_date,
    la.weekly_rate_gbp                                 AS arrangement_weekly_rate_gbp,
    la.plan_weeks                                      AS arrangement_plan_weeks,
    CASE WHEN la.account_id IS NOT NULL
         THEN TRUE ELSE FALSE END                      AS has_active_arrangement,
    ls.switch_type                                     AS last_switch_type,
    ls.switch_date                                     AS last_switch_date,
    ls.outcome                                         AS last_switch_outcome,
    CURRENT_DATE                                       AS report_date
FROM stg_accounts sa
LEFT JOIN latest_arrangement la ON sa.account_id = la.account_id
LEFT JOIN latest_switch      ls ON sa.account_id = ls.account_id
ORDER BY sa.debt_amount_gbp DESC
