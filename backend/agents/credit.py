"""Credit Score Builder Agent.

Builds a "gig-native" credit score from the unified income ledger:
- income consistency (variance / mean)
- platform tenure (months active)
- earnings growth (recent 3M vs prior 3M)
- payout frequency
- platform diversification

Output: a 300–900 score (CIBIL-style) with sub-scores. In production, the
structured payload is sent to CIBIL/Experian's commercial-credit API.
"""
from __future__ import annotations

import statistics

from coral_sql import query


def _monthly_totals(worker_id: str) -> list[float]:
    rows = query(f"""
        SELECT to_char(earned_on, '%Y-%m') AS month, SUM(amount) AS total
        FROM income_ledger
        WHERE worker_id = '{worker_id}'
        GROUP BY 1
        ORDER BY 1
    """)
    return [float(r["total"]) for r in rows]


def compute_score(worker_id: str) -> dict:
    monthlies = _monthly_totals(worker_id)
    if not monthlies:
        return {"score": 0, "band": "Insufficient data"}

    mean = statistics.mean(monthlies)
    stdev = statistics.pstdev(monthlies) if len(monthlies) > 1 else 0.0
    cv = (stdev / mean) if mean else 1.0

    # Sub-scores 0–100
    consistency = max(0, min(100, round(100 * (1 - min(cv, 0.6) / 0.6))))
    tenure_months = len(monthlies)
    tenure = max(0, min(100, round(tenure_months * 100 / 12)))

    if len(monthlies) >= 6:
        recent = statistics.mean(monthlies[-3:])
        prior = statistics.mean(monthlies[-6:-3])
        growth_pct = ((recent - prior) / prior * 100) if prior else 0.0
        growth = max(0, min(100, round(50 + growth_pct * 2)))
    else:
        growth = 50

    diversification_rows = query(f"""
        SELECT COUNT(DISTINCT platform) AS n FROM income_ledger WHERE worker_id = '{worker_id}'
    """)
    n_platforms = int(diversification_rows[0]["n"]) if diversification_rows else 1
    diversification = min(100, n_platforms * 50)

    income_band = max(0, min(100, round((mean / 50_000) * 100)))

    weights = {
        "consistency": 0.30,
        "tenure": 0.20,
        "growth": 0.20,
        "diversification": 0.10,
        "income_band": 0.20,
    }
    composite_pct = (
        consistency * weights["consistency"]
        + tenure * weights["tenure"]
        + growth * weights["growth"]
        + diversification * weights["diversification"]
        + income_band * weights["income_band"]
    )
    score = round(300 + (composite_pct / 100) * 600)

    if score >= 750:
        band, verdict = "Excellent", "Pre-approved for personal loan up to ₹2,00,000"
    elif score >= 680:
        band, verdict = "Good", "Eligible for personal loan up to ₹1,00,000"
    elif score >= 600:
        band, verdict = "Fair", "Eligible for secured credit card / small-ticket loan"
    else:
        band, verdict = "Building", "Continue 3+ months of consistent earnings to qualify"

    return {
        "score": score,
        "band": band,
        "verdict": verdict,
        "sub_scores": {
            "income_consistency": consistency,
            "platform_tenure": tenure,
            "earnings_growth": growth,
            "platform_diversification": diversification,
            "income_band": income_band,
        },
        "metrics": {
            "avg_monthly_income": round(mean),
            "income_volatility_cv": round(cv, 3),
            "tenure_months": tenure_months,
            "platforms_active": n_platforms,
        },
        "bureau_payload_sent_to": "CIBIL / Experian (mock)",
    }


def run(worker_id: str) -> dict:
    return {"agent": "CreditScoreBuilderAgent", "worker_id": worker_id, **compute_score(worker_id)}
