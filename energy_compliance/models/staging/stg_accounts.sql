{{ config(materialized='view') }}

SELECT
    account_id,
    UPPER(TRIM(customer_name))                          AS customer_name,
    UPPER(REPLACE(TRIM(postcode), ' ', ''))             AS postcode_normalised,
    LOWER(fuel_type)                                    AS fuel_type,
    LOWER(payment_method)                               AS payment_method,
    COALESCE(debt_amount, 0)                            AS debt_amount_gbp,
    COALESCE(debt_age_days, 0)                          AS debt_age_days,
    LOWER(account_status)                               AS account_status,
    CASE WHEN debt_amount  > 0   THEN TRUE ELSE FALSE END   AS has_debt,
    CASE WHEN debt_age_days > 91 THEN TRUE ELSE FALSE END   AS is_over_91_days,
    CASE WHEN payment_method = 'prepayment_meter'
          AND debt_amount > 0   THEN TRUE ELSE FALSE END    AS is_ppm_in_debt,
    created_at,
    updated_at
FROM {{ source('raw', 'accounts') }}
WHERE account_status != 'closed'
