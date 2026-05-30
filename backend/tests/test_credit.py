"""Credit score boundary + edge-case tests."""
from __future__ import annotations

import pytest

from agents.credit import compute_score


def _patch_query(monkeypatch, monthly_totals: list[float], n_platforms: int = 2):
    """Make agents.credit.query return canned results."""

    def fake_query(sql: str):
        s = sql.strip()
        if "GROUP BY 1" in s and "to_char" in s:
            return [{"month": f"2025-{i+1:02d}", "total": t}
                    for i, t in enumerate(monthly_totals)]
        if "COUNT(DISTINCT platform)" in s:
            return [{"n": n_platforms}]
        return []

    monkeypatch.setattr("agents.credit.query", fake_query)


class TestComputeScore:
    def test_no_data_returns_insufficient(self, monkeypatch):
        _patch_query(monkeypatch, [])
        out = compute_score("W001")
        assert out["score"] == 0
        assert out["band"] == "Insufficient data"

    def test_score_in_valid_range(self, monkeypatch):
        _patch_query(monkeypatch, [30_000] * 12)
        out = compute_score("W001")
        assert 300 <= out["score"] <= 900

    def test_consistent_high_earner_excellent_band(self, monkeypatch):
        _patch_query(monkeypatch, [45_000] * 12, n_platforms=3)
        out = compute_score("W001")
        assert out["score"] >= 750
        assert out["band"] == "Excellent"

    def test_low_irregular_earner_lower_band(self, monkeypatch):
        _patch_query(monkeypatch, [5_000, 25_000, 3_000, 18_000, 1_000, 12_000],
                     n_platforms=1)
        out = compute_score("W001")
        assert out["score"] < 750

    def test_sub_scores_are_percentages(self, monkeypatch):
        _patch_query(monkeypatch, [30_000] * 12)
        out = compute_score("W001")
        for k, v in out["sub_scores"].items():
            assert 0 <= v <= 100, f"{k}={v} out of range"

    def test_perfect_consistency_zero_variance(self, monkeypatch):
        _patch_query(monkeypatch, [30_000] * 12)
        out = compute_score("W001")
        assert out["sub_scores"]["income_consistency"] == 100

    def test_tenure_caps_at_100(self, monkeypatch):
        _patch_query(monkeypatch, [30_000] * 24)  # 24 months of data
        out = compute_score("W001")
        assert out["sub_scores"]["platform_tenure"] == 100

    def test_diversification_caps_at_100(self, monkeypatch):
        _patch_query(monkeypatch, [30_000] * 12, n_platforms=5)
        out = compute_score("W001")
        assert out["sub_scores"]["platform_diversification"] == 100

    def test_short_tenure_neutral_growth(self, monkeypatch):
        # Less than 6 months → growth defaults to 50
        _patch_query(monkeypatch, [30_000] * 4)
        out = compute_score("W001")
        assert out["sub_scores"]["earnings_growth"] == 50

    def test_band_matches_score(self, monkeypatch):
        cases = [
            ([45_000] * 12, 3, "Excellent"),
            ([20_000] * 6, 2, ("Good", "Fair", "Building")),  # any of these is fine
        ]
        for monthlies, n, expected in cases:
            _patch_query(monkeypatch, monthlies, n_platforms=n)
            out = compute_score("W001")
            if isinstance(expected, str):
                assert out["band"] == expected
            else:
                assert out["band"] in expected

    def test_metrics_present(self, monkeypatch):
        _patch_query(monkeypatch, [30_000] * 12)
        out = compute_score("W001")
        for key in ("avg_monthly_income", "income_volatility_cv",
                    "tenure_months", "platforms_active"):
            assert key in out["metrics"]
