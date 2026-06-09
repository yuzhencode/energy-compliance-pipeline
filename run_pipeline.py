"""
run_pipeline.py
===============
CLI entry point for the Ofgem compliance report pipeline.

Usage:
    python run_pipeline.py                      # today's date, S3 upload if configured
    python run_pipeline.py --week 2025-06-01
    python run_pipeline.py --no-upload          # skip S3 (local testing)
"""

from __future__ import annotations

import argparse
import sys
from datetime import date

import sqlalchemy

from config import config
from logger import get_logger
from pipeline.extractor   import Extractor
from pipeline.reporter    import Reporter
from pipeline.transformer import Transformer
from pipeline.validator   import Validator

logger = get_logger(__name__)


def run(report_week: date, upload: bool = True) -> int:
    logger.info("=" * 60)
    logger.info(f"Pipeline start  |  week={report_week}")
    logger.info("=" * 60)

    extractor   = Extractor(config.dsn)
    transformer = Transformer()
    validator   = Validator()
    reporter    = Reporter(config.output_dir)

    # ── Extract (raw DataFrames from mart layer SQL) ────────────────────
    raw_summary = extractor.extract_ofgem_summary()
    raw_detail  = extractor.extract_account_detail()

    # ── Transform (DataFrames → validated Pydantic models) ─────────────
    summary_rows = transformer.to_ofgem_summary(raw_summary)
    detail_rows  = transformer.to_account_detail(raw_detail)

    # ── Validate (cross-row business rules) ────────────────────────────
    val_s = validator.validate_summary(summary_rows)
    val_d = validator.validate_account_detail(detail_rows)

    if not val_s.passed or not val_d.passed:
        logger.error(f"Pipeline aborted — summary: {val_s}  detail: {val_d}")
        return 1

    # ── Report (Excel + optional S3 upload) ────────────────────────────
    output_path = reporter.generate(summary_rows, detail_rows, report_week)
    s3_uri      = reporter.upload_to_s3(output_path) if upload else None

    # ── Audit log ──────────────────────────────────────────────────────
    engine = sqlalchemy.create_engine(config.dsn)
    with engine.begin() as conn:
        conn.execute(sqlalchemy.text("""
            INSERT INTO report_runs
                (report_week, row_count, validation_passed, output_path)
            VALUES
                (:report_week, :row_count, :validation_passed, :output_path)
        """), {
            "report_week":       report_week,
            "row_count":         len(detail_rows),
            "validation_passed": True,
            "output_path":       str(s3_uri or output_path),
        })

    logger.info("=" * 60)
    logger.info(f"Pipeline complete  |  rows={len(detail_rows)}  |  out={s3_uri or output_path}")
    logger.info("=" * 60)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Ofgem compliance report pipeline")
    parser.add_argument("--week",      type=date.fromisoformat, default=date.today())
    parser.add_argument("--no-upload", action="store_true")
    args = parser.parse_args()
    sys.exit(run(args.week, upload=not args.no_upload))
