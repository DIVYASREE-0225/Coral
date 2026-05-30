"""Seeds 12 months of mock earnings across Zomato, Swiggy, Ola, Uber, Urban Company.

Each platform has its own CSV schema — that's the point. Coral's SQL Orchestrator
unifies them at query time without ETL.
"""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)

WORKERS = {
    "W001": {
        "name": "Ravi Kumar",
        "city": "Hyderabad",
        "language": "Telugu",
        "phone": "+91 98480 12345",
        "pan": "ABCPK1234R",
        "platforms": ["zomato", "swiggy"],
        "base": {"zomato": 18000, "swiggy": 14000},
    },
    "W002": {
        "name": "Priya Sharma",
        "city": "Bangalore",
        "language": "Hindi",
        "phone": "+91 99000 22222",
        "pan": "XYZPS9876K",
        "platforms": ["urbancompany"],
        "base": {"urbancompany": 45000},
    },
    "W003": {
        "name": "Arjun Patel",
        "city": "Mumbai",
        "language": "Hindi",
        "phone": "+91 98200 33333",
        "pan": "MNOPP5555T",
        "platforms": ["ola", "uber"],
        "base": {"ola": 22000, "uber": 16000},
    },
}

# Festive months get a bump (Oct/Nov/Dec)
SEASON = {1: 0.92, 2: 0.95, 3: 1.00, 4: 0.97, 5: 0.93, 6: 0.90,
          7: 0.95, 8: 1.02, 9: 1.05, 10: 1.18, 11: 1.22, 12: 1.15}


def _months(n: int = 12) -> list[date]:
    # End at March 2026 so all 12 months land in FY 2025-26 (Apr 2025 – Mar 2026),
    # which is the FY a gig worker would actually be filing taxes for right now.
    end = date(2026, 3, 1)
    months = []
    for i in range(n):
        y, m = end.year, end.month - i
        while m <= 0:
            m += 12
            y -= 1
        months.append(date(y, m, 1))
    return list(reversed(months))


def _earnings(base: int, month: date) -> int:
    factor = SEASON[month.month] * random.uniform(0.88, 1.12)
    return int(base * factor)


def seed_zomato() -> None:
    """Zomato schema: payout_id, partner_id, week_ending, orders, gross_earnings, incentives, tds, net_payout."""
    rows = []
    for wid, w in WORKERS.items():
        if "zomato" not in w["platforms"]:
            continue
        for m in _months():
            month_total = _earnings(w["base"]["zomato"], m)
            # 4 weekly payouts per month
            for week in range(4):
                week_end = m + timedelta(days=7 * (week + 1) - 1)
                gross = month_total // 4 + random.randint(-400, 400)
                incentives = int(gross * random.uniform(0.05, 0.12))
                tds = int(gross * 0.01)  # 1% TDS u/s 194O
                rows.append({
                    "payout_id": f"ZOM{m.strftime('%Y%m')}{wid}{week}",
                    "partner_id": wid,
                    "week_ending": week_end.isoformat(),
                    "orders": random.randint(85, 140),
                    "gross_earnings": gross,
                    "incentives": incentives,
                    "tds_deducted": tds,
                    "net_payout": gross + incentives - tds,
                })
    _write("zomato_payouts.csv", rows)


def seed_swiggy() -> None:
    """Swiggy schema: txn_ref, de_id, payout_date, base_pay, surge, bonus, tds, total."""
    rows = []
    for wid, w in WORKERS.items():
        if "swiggy" not in w["platforms"]:
            continue
        for m in _months():
            month_total = _earnings(w["base"]["swiggy"], m)
            for week in range(4):
                payout_date = m + timedelta(days=7 * (week + 1))
                base = month_total // 4 + random.randint(-300, 300)
                surge = int(base * random.uniform(0.08, 0.18))
                bonus = random.choice([0, 0, 0, 500, 1000])
                tds = int((base + surge) * 0.01)
                rows.append({
                    "txn_ref": f"SWGY-{m.strftime('%y%m')}-{wid}-W{week+1}",
                    "de_id": wid,
                    "payout_date": payout_date.isoformat(),
                    "base_pay": base,
                    "surge": surge,
                    "bonus": bonus,
                    "tds": tds,
                    "total": base + surge + bonus - tds,
                })
    _write("swiggy_payouts.csv", rows)


def seed_ola() -> None:
    """Ola schema: trip_settlement_id, driver_id, settlement_date, fare, commission, incentive, net."""
    rows = []
    for wid, w in WORKERS.items():
        if "ola" not in w["platforms"]:
            continue
        for m in _months():
            month_total = _earnings(w["base"]["ola"], m)
            # Ola settles weekly
            for week in range(4):
                sd = m + timedelta(days=7 * week + 5)
                fare = month_total // 4 + random.randint(-500, 500)
                commission = int(fare * 0.20)
                incentive = int(fare * random.uniform(0.06, 0.14))
                rows.append({
                    "trip_settlement_id": f"OLA{wid}{m.strftime('%Y%m')}W{week}",
                    "driver_id": wid,
                    "settlement_date": sd.isoformat(),
                    "gross_fare": fare,
                    "platform_commission": commission,
                    "incentive": incentive,
                    "net_amount": fare - commission + incentive,
                })
    _write("ola_settlements.csv", rows)


def seed_uber() -> None:
    """Uber schema: weekly_statement_id, partner_uuid, week_start, week_end, trips, earnings_breakdown_json."""
    rows = []
    for wid, w in WORKERS.items():
        if "uber" not in w["platforms"]:
            continue
        for m in _months():
            month_total = _earnings(w["base"]["uber"], m)
            for week in range(4):
                ws = m + timedelta(days=7 * week)
                we = ws + timedelta(days=6)
                weekly = month_total // 4 + random.randint(-400, 400)
                fare = int(weekly * 0.78)
                tips = int(weekly * 0.05)
                promo = int(weekly * 0.17)
                rows.append({
                    "weekly_statement_id": f"UBR-{wid}-{ws.strftime('%Y%m%d')}",
                    "partner_uuid": wid,
                    "week_start": ws.isoformat(),
                    "week_end": we.isoformat(),
                    "trips": random.randint(72, 115),
                    "fare_earnings": fare,
                    "tips": tips,
                    "promotions": promo,
                    "net_earnings": weekly,
                })
    _write("uber_statements.csv", rows)


def seed_urbancompany() -> None:
    """Urban Company schema: job_id, professional_id, job_date, service, customer_paid, uc_fee, professional_payout."""
    rows = []
    for wid, w in WORKERS.items():
        if "urbancompany" not in w["platforms"]:
            continue
        for m in _months():
            month_total = _earnings(w["base"]["urbancompany"], m)
            # ~30 jobs per month
            n_jobs = random.randint(28, 38)
            per_job = month_total / n_jobs
            for j in range(n_jobs):
                day = m + timedelta(days=random.randint(0, 27))
                customer_paid = int(per_job / 0.75 + random.randint(-150, 150))
                uc_fee = int(customer_paid * 0.25)
                rows.append({
                    "job_id": f"UC{m.strftime('%Y%m')}{wid}J{j:02d}",
                    "professional_id": wid,
                    "job_date": day.isoformat(),
                    "service": random.choice(["Salon at Home", "Spa", "Hair Treatment", "Bridal"]),
                    "customer_paid": customer_paid,
                    "uc_fee": uc_fee,
                    "professional_payout": customer_paid - uc_fee,
                })
    _write("urbancompany_jobs.csv", rows)


def seed_workers() -> None:
    rows = [{"worker_id": wid, **{k: v for k, v in w.items() if k not in ("base",)}, "platforms": ",".join(w["platforms"])}
            for wid, w in WORKERS.items()]
    _write("workers.csv", rows)


def _write(name: str, rows: list[dict]) -> None:
    if not rows:
        return
    path = DATA / name
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {len(rows):>4} rows → {path.name}")


def main() -> None:
    print("Seeding GigProof mock data…")
    seed_workers()
    seed_zomato()
    seed_swiggy()
    seed_ola()
    seed_uber()
    seed_urbancompany()
    print("Done.")


if __name__ == "__main__":
    main()
