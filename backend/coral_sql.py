"""Coral SQL Orchestrator.

Shells out to the `coral` CLI (`coral sql --format json`) for every query.
Each platform spec is installed as a Coral source (`zomato.payouts`,
`swiggy.payouts`, `ola.settlements`, `uber.weekly_statements`,
`urbancompany.jobs`, `gigproof.workers`).

Cross-source queries reference a unified `income_ledger` CTE that this
module prepends automatically when the SQL mentions `income_ledger`. Coral
file-backed sources can't define views, so the CTE is the workaround — and
it stays a single Coral query, no in-process joining.
"""
from __future__ import annotations

import asyncio
import json
import re
import shutil
import subprocess
from functools import lru_cache

CORAL_BIN = shutil.which("coral") or "coral"

# (coral_table, worker_col, date_col, amount_col, label)
PLATFORMS = [
    ("zomato.payouts",            "partner_id",      "week_ending",     "net_payout",          "Zomato"),
    ("swiggy.payouts",            "de_id",           "payout_date",     "total",               "Swiggy"),
    ("ola.settlements",           "driver_id",       "settlement_date", "net_amount",          "Ola"),
    ("uber.weekly_statements",    "partner_uuid",    "week_end",        "net_earnings",        "Uber"),
    ("urbancompany.jobs",         "professional_id", "job_date",        "professional_payout", "UrbanCompany"),
]

WORKERS_TABLE = "gigproof.workers"


@lru_cache(maxsize=1)
def _income_ledger_cte() -> str:
    parts = []
    for table, worker_col, date_col, amount_col, label in PLATFORMS:
        parts.append(
            f"SELECT '{label}' AS platform, "
            f"{worker_col} AS worker_id, "
            f"CAST({date_col} AS TIMESTAMP) AS earned_on, "
            f"CAST({amount_col} AS DOUBLE) AS amount "
            f"FROM {table}"
        )
    return "income_ledger AS (\n  " + "\n  UNION ALL\n  ".join(parts) + "\n)"


_INCOME_LEDGER_REF = re.compile(r"\bincome_ledger\b", re.IGNORECASE)


def _wrap(sql: str) -> str:
    """Prepend the income_ledger CTE if the query references it."""
    stripped = sql.strip().rstrip(";")
    if not _INCOME_LEDGER_REF.search(stripped):
        return stripped
    cte = _income_ledger_cte()
    if stripped[:5].lower() == "with ":
        return "WITH " + cte + ",\n" + stripped[5:]
    return "WITH " + cte + "\n" + stripped


def query(sql: str) -> list[dict]:
    """Run a read-only SQL query through `coral sql --format json` (sync)."""
    wrapped = _wrap(sql)
    result = subprocess.run(
        [CORAL_BIN, "sql", wrapped, "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"coral sql failed (exit {result.returncode}): {result.stderr.strip() or result.stdout.strip()}"
        )
    out = result.stdout.strip()
    if not out:
        return []
    return json.loads(out)


async def aquery(sql: str) -> list[dict]:
    """Async variant of query() using asyncio subprocess. Lets multiple
    queries run concurrently via asyncio.gather."""
    wrapped = _wrap(sql)
    proc = await asyncio.create_subprocess_exec(
        CORAL_BIN, "sql", wrapped, "--format", "json",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        err = (stderr.decode().strip() or stdout.decode().strip())
        raise RuntimeError(f"coral sql failed (exit {proc.returncode}): {err}")
    out = stdout.decode().strip()
    if not out:
        return []
    return json.loads(out)


async def aquery_many(sqls: list[str]) -> list[list[dict]]:
    """Run multiple queries concurrently. Returns results in input order."""
    return await asyncio.gather(*(aquery(s) for s in sqls))


def list_tables() -> list[dict]:
    """Schema introspection via Coral's catalog tables."""
    rows = query(
        "SELECT schema_name, table_name, column_name, data_type "
        "FROM coral.columns "
        "ORDER BY schema_name, table_name, ordinal_position"
    )
    by_table: dict[str, list[dict]] = {}
    for r in rows:
        qualified = f"{r['schema_name']}.{r['table_name']}"
        by_table.setdefault(qualified, []).append(
            {"name": r["column_name"], "type": r["data_type"]}
        )
    out = [{"name": name, "columns": cols} for name, cols in by_table.items()]
    out.append({
        "name": "income_ledger (CTE)",
        "columns": [
            {"name": "platform", "type": "Utf8"},
            {"name": "worker_id", "type": "Utf8"},
            {"name": "earned_on", "type": "Timestamp"},
            {"name": "amount", "type": "Float64"},
        ],
    })
    return out
