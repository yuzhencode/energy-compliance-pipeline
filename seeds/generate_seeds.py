"""
seeds/generate_seeds.py
=======================
Generates synthetic seed data using Faker (en_GB locale).
All data is fictitious — no real customer information.

Usage:
    python seeds/generate_seeds.py              # 500 accounts (default)
    python seeds/generate_seeds.py --rows 1000
    python seeds/generate_seeds.py --truncate   # wipe tables first
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import date, timedelta
from pathlib import Path

import sqlalchemy
from faker import Faker

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config  # noqa: E402

fake = Faker("en_GB")

FUEL_TYPES      = ["gas", "electric", "dual"]
PAYMENT_METHODS = ["direct_debit", "direct_debit", "prepayment_meter", "cash", "other"]
STATUSES        = ["active", "active", "active", "disputed", "closed"]
SWITCH_TYPES    = ["prepayment", "credit", "emergency"]
SWITCH_OUTCOMES = ["success", "success", "failed", "pending"]
ARRANGEMENT_STATUS = ["active", "active", "completed", "broken"]


def _rdate(days_back: int = 730) -> date:
    return date.today() - timedelta(days=random.randint(0, days_back))


def gen_accounts(n: int) -> list[dict]:
    return [
        {
            "account_id":     f"ACC{i+1:06d}",
            "customer_name":  fake.name(),
            "postcode":       fake.postcode(),
            "fuel_type":      random.choice(FUEL_TYPES),
            "payment_method": random.choice(PAYMENT_METHODS),
            "debt_amount":    round(random.uniform(0, 3000), 2),
            "debt_age_days":  random.randint(0, 400),
            "account_status": random.choice(STATUSES),
        }
        for i in range(n)
    ]


def gen_arrangements(account_ids: list[str]) -> list[dict]:
    rows = []
    for acc_id in account_ids:
        if random.random() < 0.4:           # 40% of accounts have an arrangement
            rows.append({
                "account_id":       acc_id,
                "arrangement_date": _rdate(365),
                "weekly_rate_gbp":  round(random.uniform(5, 50), 2),
                "plan_weeks":       random.randint(10, 104),
                "status":           random.choice(ARRANGEMENT_STATUS),
            })
    return rows


def gen_switch_events(account_ids: list[str]) -> list[dict]:
    rows = []
    for acc_id in account_ids:
        for _ in range(random.randint(0, 3)):
            rows.append({
                "account_id":  acc_id,
                "switch_type": random.choice(SWITCH_TYPES),
                "switch_date": _rdate(),
                "actioned_by": fake.name(),
                "outcome":     random.choice(SWITCH_OUTCOMES),
            })
    return rows


def load(engine: sqlalchemy.Engine, accounts: list, arrangements: list, events: list) -> None:
    with engine.begin() as conn:
        conn.execute(sqlalchemy.text("""
            INSERT INTO accounts
                (account_id, customer_name, postcode, fuel_type, payment_method,
                 debt_amount, debt_age_days, account_status)
            VALUES
                (:account_id, :customer_name, :postcode, :fuel_type, :payment_method,
                 :debt_amount, :debt_age_days, :account_status)
            ON CONFLICT (account_id) DO NOTHING
        """), accounts)

        if arrangements:
            conn.execute(sqlalchemy.text("""
                INSERT INTO debt_repayment_arrangements
                    (account_id, arrangement_date, weekly_rate_gbp, plan_weeks, status)
                VALUES
                    (:account_id, :arrangement_date, :weekly_rate_gbp, :plan_weeks, :status)
            """), arrangements)

        if events:
            conn.execute(sqlalchemy.text("""
                INSERT INTO remote_switch_events
                    (account_id, switch_type, switch_date, actioned_by, outcome)
                VALUES
                    (:account_id, :switch_type, :switch_date, :actioned_by, :outcome)
            """), events)

    print(
        f"Seeded {len(accounts)} accounts, "
        f"{len(arrangements)} arrangements, "
        f"{len(events)} switch events."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed energy compliance database")
    parser.add_argument("--rows",     type=int,  default=500)
    parser.add_argument("--truncate", action="store_true")
    args = parser.parse_args()

    engine = sqlalchemy.create_engine(config.dsn)

    if args.truncate:
        with engine.begin() as conn:
            conn.execute(sqlalchemy.text(
                "TRUNCATE remote_switch_events, debt_repayment_arrangements, accounts "
                "RESTART IDENTITY CASCADE"
            ))
        print("Tables truncated.")

    accounts     = gen_accounts(args.rows)
    arrangements = gen_arrangements([a["account_id"] for a in accounts])
    events       = gen_switch_events([a["account_id"] for a in accounts])
    load(engine, accounts, arrangements, events)


if __name__ == "__main__":
    main()
