{{ config(materialized='view') }}

SELECT
    arrangement_id,
    account_id,
    arrangement_date,
    COALESCE(weekly_rate_gbp, 0)        AS weekly_rate_gbp,
    COALESCE(plan_weeks, 0)             AS plan_weeks,
    LOWER(status)                       AS arrangement_status,
    ROW_NUMBER() OVER (
        PARTITION BY account_id
        ORDER BY arrangement_date DESC
    )                                   AS recency_rank,
    created_at
FROM {{ source('raw', 'debt_repayment_arrangements') }}
WHERE status = 'active'
