"""Platform Ingestion Agent.

Aggregates per-worker earnings across all 5 platforms via the unified
`income_ledger` CTE (defined in coral_sql._wrap and prepended automatically).
"""
from __future__ import annotations

from coral_sql import query


def monthly_ledger(worker_id: str) -> list[dict]:
    return query(f"""
        SELECT to_char(earned_on, '%Y-%m') AS month,
               platform,
               SUM(amount) AS earnings
        FROM income_ledger
        WHERE worker_id = '{worker_id}'
        GROUP BY 1, 2
        ORDER BY 1, 2
    """)


def platform_breakdown(worker_id: str) -> list[dict]:
    return query(f"""
        SELECT platform,
               COUNT(*) AS payouts,
               SUM(amount) AS total_earnings,
               AVG(amount) AS avg_payout,
               MIN(earned_on) AS first_payout,
               MAX(earned_on) AS last_payout
        FROM income_ledger
        WHERE worker_id = '{worker_id}'
        GROUP BY platform
        ORDER BY total_earnings DESC
    """)


def annual_summary(worker_id: str) -> dict:
    rows = query(f"""
        SELECT SUM(amount) AS gross_annual,
               COUNT(*) AS total_payouts,
               COUNT(DISTINCT platform) AS platforms,
               MIN(earned_on) AS earliest,
               MAX(earned_on) AS latest
        FROM income_ledger
        WHERE worker_id = '{worker_id}'
    """)
    return rows[0] if rows else {}


def run(worker_id: str) -> dict:
    return {
        "agent": "PlatformIngestionAgent",
        "worker_id": worker_id,
        "summary": annual_summary(worker_id),
        "by_platform": platform_breakdown(worker_id),
        "by_month": monthly_ledger(worker_id),
    }
