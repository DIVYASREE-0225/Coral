"""Tests for the coral_sql wrapper — focuses on _wrap CTE injection logic.

These run without `coral` installed; we don't actually execute queries.
"""
from __future__ import annotations

import pytest

from coral_sql import _wrap, _income_ledger_cte


class TestWrap:
    def test_passthrough_when_no_income_ledger(self):
        sql = "SELECT * FROM gigproof.workers WHERE worker_id = 'W001'"
        assert _wrap(sql) == sql

    def test_strips_trailing_semicolon(self):
        assert _wrap("SELECT 1;") == "SELECT 1"

    def test_strips_whitespace(self):
        assert _wrap("  SELECT 1  \n") == "SELECT 1"

    def test_prepends_cte_when_referenced(self):
        out = _wrap("SELECT * FROM income_ledger LIMIT 10")
        assert out.startswith("WITH income_ledger AS")
        assert "SELECT * FROM income_ledger LIMIT 10" in out

    def test_handles_existing_with_clause(self):
        sql = "WITH monthly AS (SELECT 1) SELECT * FROM income_ledger"
        out = _wrap(sql)
        assert out.startswith("WITH income_ledger AS")
        assert "monthly AS" in out
        # Both CTEs should remain
        assert out.count("AS (") >= 2

    def test_lowercase_with_clause(self):
        sql = "with monthly as (select 1) select * from income_ledger"
        out = _wrap(sql)
        assert out.startswith("WITH income_ledger AS")
        assert "monthly as" in out

    def test_word_boundary_respected(self):
        # Column literally named "income_ledger_x" should NOT trigger CTE injection
        sql = "SELECT income_ledger_x FROM some_table"
        assert _wrap(sql) == sql

    def test_word_boundary_quoted_identifier(self):
        sql = "SELECT my_income_ledger_total FROM some_table"
        assert _wrap(sql) == sql

    def test_case_insensitive_match(self):
        out = _wrap("SELECT * FROM Income_Ledger")
        assert out.startswith("WITH income_ledger AS")


class TestIncomeLedgerCTE:
    def test_cte_unions_all_five_platforms(self):
        cte = _income_ledger_cte()
        for label in ("Zomato", "Swiggy", "Ola", "Uber", "UrbanCompany"):
            assert f"'{label}'" in cte

    def test_cte_starts_with_alias(self):
        assert _income_ledger_cte().startswith("income_ledger AS (")

    def test_cte_contains_four_unions(self):
        # 5 SELECTs joined by 4 UNION ALLs
        assert _income_ledger_cte().count("UNION ALL") == 4

    def test_cte_normalises_columns(self):
        cte = _income_ledger_cte()
        for col in ("platform", "worker_id", "earned_on", "amount"):
            assert col in cte
