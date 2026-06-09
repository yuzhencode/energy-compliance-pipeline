"""
pipeline/extractor.py
=====================
Runs SQL from sql/marts/ against the database and returns raw DataFrames.
No business logic here — transformation happens in transformer.py.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import sqlalchemy
from sqlalchemy import text

from logger import get_logger

logger  = get_logger(__name__)
SQL_DIR = Path(__file__).parent.parent / "sql"


class Extractor:
    def __init__(self, dsn: str) -> None:
        self.engine = sqlalchemy.create_engine(dsn)

    def _sql(self, *parts: str) -> str:
        """Load a SQL file relative to sql/."""
        return (SQL_DIR.joinpath(*parts)).read_text()

    def extract_ofgem_summary(self) -> pd.DataFrame:
        logger.info("Extracting Ofgem summary (mart layer)")
        df = pd.read_sql(text(self._sql("marts", "ofgem_summary.sql")), self.engine)
        logger.info(f"Summary rows: {len(df)}")
        return df

    def extract_account_detail(self) -> pd.DataFrame:
        logger.info("Extracting account detail (mart layer)")
        df = pd.read_sql(text(self. _sql("marts", "account_detail.sql")), self.engine)
        logger.info(f"Account detail rows: {len(df)}")
        return df
