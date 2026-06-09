from datetime import date
import pytest
from pipeline.models import AccountDetailRow, OfgemSummaryRow


@pytest.fixture
def summary_row():
    return OfgemSummaryRow(
        avg_debt_no_arrangement_gbp=320.50,
        avg_debt_with_arrangement_gbp=180.00,
        pct_repaying_via_ppm=22.5,
        accounts_with_debt=400,
        accounts_no_arrangement=260,
        total_debt_over_91_days_gbp=85000.00,
        reporting_quarter=date(2025, 4, 1),
        report_date=date(2025, 6, 1),
    )


@pytest.fixture
def detail_rows():
    base = dict(
        fuel_type="gas",
        payment_method="direct_debit",
        debt_amount_gbp=500.0,
        debt_age_days=45,
        is_over_91_days=False,
        account_status="active",
        has_active_arrangement=False,
        arrangement_date=None,
        arrangement_weekly_rate_gbp=None,
        arrangement_plan_weeks=None,
        last_switch_type=None,
        last_switch_date=None,
        last_switch_outcome=None,
        report_date=date(2025, 6, 1),
    )
    return [
        AccountDetailRow(account_id="ACC000001", customer_name="Alice Smith",
                         postcode="NG11AA", **base),
        AccountDetailRow(account_id="ACC000002", customer_name="Bob Jones",
                         postcode="NG22BB", **{**base, "debt_amount_gbp": 320.0}),
    ]
