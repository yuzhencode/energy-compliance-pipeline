"""Tests for cross-row business-rule validation (pipeline/validator.py)."""

from datetime import date
import pytest
from pipeline.models import AccountDetailRow, OfgemSummaryRow
from pipeline.validator import Validator


class TestValidateSummary:
    def test_valid_passes(self, summary_row):
        result = Validator().validate_summary([summary_row])
        assert result.passed

    def test_empty_list_fails(self):
        result = Validator().validate_summary([])
        assert not result.passed
        assert any("no rows" in e for e in result.errors)

    def test_zero_accounts_with_debt_fails(self, summary_row):
        summary_row.accounts_with_debt = 0
        result = Validator().validate_summary([summary_row])
        assert not result.passed

    def test_no_arrangement_exceeds_total_fails(self, summary_row):
        summary_row.accounts_no_arrangement = summary_row.accounts_with_debt + 1
        result = Validator().validate_summary([summary_row])
        assert not result.passed


class TestValidateAccountDetail:
    def test_valid_passes(self, detail_rows):
        result = Validator().validate_account_detail(detail_rows)
        assert result.passed

    def test_empty_list_fails(self):
        result = Validator().validate_account_detail([])
        assert not result.passed

    def test_duplicate_ids_fail(self, detail_rows):
        duped = detail_rows + [detail_rows[0]]
        result = Validator().validate_account_detail(duped)
        assert not result.passed
        assert any("Duplicate" in e for e in result.errors)
