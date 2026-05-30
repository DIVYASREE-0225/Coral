"""Tax filing slab math + FY window."""
from __future__ import annotations

from datetime import date

import pytest

from agents.tax_filing import (
    NEW_REGIME_SLABS,
    PRESUMPTIVE_RATE_44AD,
    _fy_window,
    _slab_tax,
    compute_itr4,
)


class TestSlabTax:
    def test_zero_income(self):
        assert _slab_tax(0) == 0

    def test_below_basic_exemption(self):
        # ₹2L is below the ₹3L exemption
        assert _slab_tax(200_000) == 0

    def test_at_exemption_boundary(self):
        assert _slab_tax(300_000) == 0

    def test_lower_slab(self):
        # ₹5L: first 3L tax-free, next 2L @ 5% = 10,000
        assert _slab_tax(500_000) == 10_000

    def test_700k_boundary(self):
        # ₹7L: 3L*0% + 4L*5% = 20,000
        assert _slab_tax(700_000) == 20_000

    def test_million(self):
        # ₹10L: 3L*0% + 4L*5% + 3L*10% = 0 + 20,000 + 30,000 = 50,000
        assert _slab_tax(1_000_000) == 50_000

    def test_top_slab(self):
        # ₹20L: 3L*0% + 4L*5% + 3L*10% + 2L*15% + 3L*20% + 5L*30%
        # = 0 + 20k + 30k + 30k + 60k + 150k = 290,000
        assert _slab_tax(2_000_000) == 290_000

    def test_slabs_monotonically_increase(self):
        prev = -1
        for income in range(0, 3_000_000, 50_000):
            t = _slab_tax(income)
            assert t >= prev, f"Tax decreased at {income}"
            prev = t


class TestFYWindow:
    def test_returns_fy_2025_26(self):
        # Currently hardcoded — flag this when the comment expires post-Sep 2026.
        start, end = _fy_window()
        assert start == date(2025, 4, 1)
        assert end == date(2026, 3, 31)

    def test_window_spans_one_year(self):
        start, end = _fy_window()
        assert (end - start).days == 364


class TestComputeITR4:
    @pytest.fixture
    def patched_query(self, monkeypatch):
        """Inject deterministic SQL responses."""

        def make(gross: float, zomato_tds: float = 0, swiggy_tds: float = 0):
            def fake_query(sql: str):
                s = sql.strip()
                if "SUM(amount)" in s and "income_ledger" in s:
                    return [{"gross": gross}]
                if "tds_deducted" in s and "zomato.payouts" in s:
                    return [{"t": zomato_tds}]
                if "swiggy.payouts" in s:
                    return [{"t": swiggy_tds}]
                return []

            monkeypatch.setattr("agents.tax_filing.query", fake_query)

        return make

    def test_low_income_zero_tax(self, patched_query):
        # Gross ₹4L → presumed = ₹24k → below exemption → tax 0
        patched_query(gross=400_000)
        out = compute_itr4("W001")
        assert out["presumed_income"] == 24_000
        assert out["total_tax_liability"] == 0
        assert out["tax_payable"] == 0

    def test_form_and_section_set(self, patched_query):
        patched_query(gross=400_000)
        out = compute_itr4("W001")
        assert out["form"] == "ITR-4 (Sugam)"
        assert "44AD" in out["section"]

    def test_refund_when_tds_exceeds_liability(self, patched_query):
        patched_query(gross=400_000, zomato_tds=2_000)
        out = compute_itr4("W001")
        assert out["refund_due"] == 2_000
        assert out["tax_payable"] == 0

    def test_high_income_triggers_gst(self, patched_query):
        patched_query(gross=25_000_000)
        out = compute_itr4("W001")
        assert out["gst_registration_required"] is True

    def test_low_income_no_gst(self, patched_query):
        patched_query(gross=500_000)
        out = compute_itr4("W001")
        assert out["gst_registration_required"] is False

    def test_advance_tax_schedule_has_four_instalments(self, patched_query):
        patched_query(gross=10_000_000)  # high income to ensure non-zero payable
        out = compute_itr4("W001")
        assert len(out["advance_tax_schedule"]) == 4
        assert [s["percent"] for s in out["advance_tax_schedule"]] == [15, 45, 75, 100]

    def test_presumptive_rate_constant(self):
        assert PRESUMPTIVE_RATE_44AD == 0.06
