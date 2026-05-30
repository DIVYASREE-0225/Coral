"""SQL Orchestrator Agent — Coral's superpower.

Runs cross-source SQL across all platform tables in a single query.
Provides curated example queries that demonstrate joins/aggregations
no single-tool app (ClearTax, Quicko) can do.
"""
from __future__ import annotations

from coral_sql import list_tables, query

EXAMPLE_QUERIES = [
    {
        "name": "Workers earning ₹25K-₹40K/month for 6+ months who haven't filed ITR",
        "sql": """
            WITH monthly AS (
              SELECT worker_id,
                     to_char(earned_on, '%Y-%m') AS month,
                     SUM(amount) AS total
              FROM income_ledger
              GROUP BY 1, 2
            ),
            qualifying AS (
              SELECT worker_id, COUNT(*) AS qualifying_months
              FROM monthly
              WHERE total BETWEEN 25000 AND 40000
              GROUP BY worker_id
              HAVING COUNT(*) >= 6
            )
            SELECT w.worker_id, w.name, w.city, q.qualifying_months,
                   'Not filed (mock)' AS itr_status
            FROM qualifying q JOIN gigproof.workers w USING (worker_id)
            ORDER BY q.qualifying_months DESC
        """.strip(),
    },
    {
        "name": "Cross-platform monthly trend per worker",
        "sql": """
            SELECT worker_id,
                   to_char(earned_on, '%Y-%m') AS month,
                   platform,
                   SUM(amount) AS earnings
            FROM income_ledger
            GROUP BY 1, 2, 3
            ORDER BY 1, 2, 3
        """.strip(),
    },
    {
        "name": "Festive-season uplift (Oct-Dec vs Jan-Mar)",
        "sql": """
            SELECT worker_id,
                   SUM(CASE WHEN EXTRACT(MONTH FROM earned_on) IN (10,11,12) THEN amount ELSE 0 END) AS festive,
                   SUM(CASE WHEN EXTRACT(MONTH FROM earned_on) IN (1,2,3) THEN amount ELSE 0 END) AS lean
            FROM income_ledger
            GROUP BY worker_id
        """.strip(),
    },
    {
        "name": "Platform diversification + total annual income",
        "sql": """
            SELECT w.worker_id, w.name, w.city,
                   COUNT(DISTINCT il.platform) AS platforms,
                   ROUND(SUM(il.amount)) AS gross_annual
            FROM gigproof.workers w
            LEFT JOIN income_ledger il USING (worker_id)
            GROUP BY 1, 2, 3
            ORDER BY gross_annual DESC
        """.strip(),
    },
]


def schemas() -> list[dict]:
    return list_tables()


def examples() -> list[dict]:
    return EXAMPLE_QUERIES


def run_query(sql: str) -> dict:
    rows = query(sql)
    return {"rows": rows, "row_count": len(rows)}


def run() -> dict:
    return {
        "agent": "SQLOrchestrator",
        "tables": [t["name"] for t in schemas()],
        "examples": [e["name"] for e in EXAMPLE_QUERIES],
    }
