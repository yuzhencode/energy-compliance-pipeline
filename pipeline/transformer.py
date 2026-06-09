"""
pipeline/transformer.py
=======================
Converts raw DataFrames from the extractor into lists of validated Pydantic
models (OfgemSummaryRow, AccountDetailRow).

This is the schema-enforcement boundary: if a row doesn't conform to the
model, a ValidationError is raised here rather than silently passing bad
data downstream to the reporter.
"""

from __future__ import annotations

from typing import List

import pandas as pd
from pydantic import ValidationError

from logger import get_logger
from pipeline.models import AccountDetailRow, OfgemSummaryRow

logger = get_logger(__name__)


class Transformer:
    def to_ofgem_summary(self, df: pd.DataFrame) -> List[OfgemSummaryRow]:
        logger.info("Transforming Ofgem summary into typed models")
        rows: List[OfgemSummaryRow] = []
        errors = 0
        for _, row in df.iterrows():
            try:
                rows.append(OfgemSummaryRow(**row.to_dict()))
            except ValidationError as exc:
                errors += 1
                logger.error(f"Summary row validation error: {exc}")
        if errors:
            raise ValueError(f"{errors} summary row(s) failed Pydantic validation")
        logger.info(f"Summary: {len(rows)} row(s) validated")
        return rows

    def to_account_detail(self, df: pd.DataFrame) -> List[AccountDetailRow]:
        logger.info("Transforming account detail into typed models")
        rows: List[AccountDetailRow] = []
        errors = 0
        for _, row in df.iterrows():
            try:
                rows.append(AccountDetailRow(**row.to_dict()))
            except ValidationError as exc:
                errors += 1
                logger.error(f"Account row validation error — {row.get('account_id', '?')}: {exc}")
        if errors:
            raise ValueError(f"{errors} account row(s) failed Pydantic validation")
        logger.info(f"Account detail: {len(rows)} row(s) validated")
        return rows
