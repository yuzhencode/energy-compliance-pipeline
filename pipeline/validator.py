"""
pipeline/validator.py
=====================
Business-rule validation on top of the Pydantic type checks.

Pydantic (in transformer.py) enforces field types and constraints.
This validator enforces cross-row business rules:
  - Summary must have exactly one row
  - Total debt >91 days must be > 0 if there are accounts with debt
  - No duplicate account IDs in detail
  - PPM % must be between 0 and 100
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from logger import get_logger
from pipeline.models import AccountDetailRow, OfgemSummaryRow

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    passed: bool = True
    errors: List[str] = field(default_factory=list)

    def fail(self, msg: str) -> None:
        self.passed = False
        self.errors.append(msg)
        logger.error(f"Validation FAILED: {msg}")

    def __str__(self) -> str:
        if self.passed:
            return "PASSED"
        return f"FAILED — {'; '.join(self.errors)}"


class Validator:
    def validate_summary(self, rows: List[OfgemSummaryRow]) -> ValidationResult:
        result = ValidationResult()

        if not rows:
            result.fail("Ofgem summary returned no rows")
            return result

        if len(rows) != 1:
            result.fail(f"Expected exactly 1 summary row, got {len(rows)}")

        row = rows[0]

        if row.accounts_with_debt == 0:
            result.fail("accounts_with_debt is 0 — likely a data or filter issue")

        if row.accounts_no_arrangement > row.accounts_with_debt:
            result.fail(
                f"accounts_no_arrangement ({row.accounts_no_arrangement}) "
                f"exceeds accounts_with_debt ({row.accounts_with_debt})"
            )

        if row.pct_repaying_via_ppm is not None:
            if not (0 <= row.pct_repaying_via_ppm <= 100):
                result.fail(f"pct_repaying_via_ppm out of range: {row.pct_repaying_via_ppm}")

        if result.passed:
            logger.info("Summary validation PASSED")
        return result

    def validate_account_detail(self, rows: List[AccountDetailRow]) -> ValidationResult:
        result = ValidationResult()

        if not rows:
            result.fail("Account detail returned no rows")
            return result

        # Duplicate account IDs
        ids = [r.account_id for r in rows]
        seen: set = set()
        dupes = {i for i in ids if i in seen or seen.add(i)}  # type: ignore[func-returns-value]
        if dupes:
            result.fail(f"Duplicate account IDs found: {dupes}")

        # Negative debt
        neg = [r.account_id for r in rows if r.debt_amount_gbp < 0]
        if neg:
            result.fail(f"Negative debt_amount_gbp on accounts: {neg}")

        if result.passed:
            logger.info(f"Account detail validation PASSED ({len(rows)} rows)")
        return result
