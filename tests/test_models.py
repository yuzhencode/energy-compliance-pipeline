"""Tests for Pydantic model validation (pipeline/models.py)."""

from datetime import date
import pytest
from pydantic import ValidationError
from pipeline.models import AccountDetailRow, OfgemSummaryRow, StagedAccount


class TestStagedAccount:
    def _valid(self, **overrides):
        base = dict(
            account_id="ACC000001",
            customer_name="Alice Smith",
            postcode="NG11AA",
            fuel_type="gas",
            payment_method="direct_debit",
            debt_amount_gbp=200.0,
            debt_age_days=50,
            account_status="active",
            has_debt=True,
            is_over_91_days=False,
            is_ppm_in_debt=False,
        )
        return StagedAccount(**{**base, **overrides})

    def test_valid_account(self):
        acc = self._valid()
        assert acc.account_id == "ACC000001"

    def test_negative_debt_raises(self):
        with pytest.raises(ValidationError):
            self._valid(debt_amount_gbp=-1.0)

    def test_invalid_fuel_type_raises(self):
        with pytest.raises(ValidationError):
            self._valid(fuel_type="oil")

    def test_empty_account_id_raises(self):
        with pytest.raises(ValidationError):
            self._valid(account_id="   ")

    def test_inconsistent_has_debt_flag_raises(self):
        with pytest.raises(ValidationError):
            self._valid(has_debt=True, debt_amount_gbp=0.0)

    def test_inconsistent_over_91_flag_raises(self):
        with pytest.raises(ValidationError):
            self._valid(is_over_91_days=True, debt_age_days=30)


class TestOfgemSummaryRow:
    def _valid(self, **overrides):
        base = dict(
            avg_debt_no_arrangement_gbp=300.0,
            avg_debt_with_arrangement_gbp=150.0,
            pct_repaying_via_ppm=20.0,
            accounts_with_debt=500,
            accounts_no_arrangement=300,
            total_debt_over_91_days_gbp=75000.0,
            reporting_quarter=date(2025, 4, 1),
            report_date=date(2025, 6, 1),
        )
        return OfgemSummaryRow(**{**base, **overrides})

    def test_valid_summary(self):
        row = self._valid()
        assert row.accounts_with_debt == 500

    def test_negative_debt_raises(self):
        with pytest.raises(ValidationError):
            self._valid(avg_debt_no_arrangement_gbp=-10.0)

    def test_ppm_over_100_raises(self):
        with pytest.raises(ValidationError):
            self._valid(pct_repaying_via_ppm=101.0)
