from __future__ import annotations

import pandas as pd
from pathlib import Path

PRESUMPTIVE_RATE_44AD = 0.06
CESS_RATE = 0.04

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


# =========================
# LOAD LEDGER
# =========================
def load_income_ledger():

    path = DATA_DIR / "income_ledger.csv"

    if not path.exists():
        return pd.DataFrame()

    return pd.read_csv(path)


# =========================
# GROSS INCOME
# =========================
def gross_for_fy(worker_id: str) -> float:

    df = load_income_ledger()

    if df.empty:
        return 0.0

    worker_rows = df[df["worker_id"] == worker_id]

    return float(worker_rows["amount"].sum())


# =========================
# TDS
# =========================
def tds_already_deducted(worker_id: str) -> float:

    df = load_income_ledger()

    if df.empty:
        return 0.0

    if "tds_deducted" not in df.columns:
        return 0.0

    worker_rows = df[df["worker_id"] == worker_id]

    return float(worker_rows["tds_deducted"].sum())


# =========================
# TAX CALCULATION
# =========================
def compute_itr4(worker_id: str):

    gross = gross_for_fy(worker_id)

    presumed_income = gross * PRESUMPTIVE_RATE_44AD

    tax_before_cess = presumed_income * 0.10

    cess = tax_before_cess * CESS_RATE

    total_tax = tax_before_cess + cess

    tds = tds_already_deducted(worker_id)

    payable = max(0.0, total_tax - tds)

    refund = max(0.0, tds - total_tax)

    return {
        "fy": "2025-26",
        "form": "ITR-4 (Sugam)",
        "section": "44AD presumptive taxation",
        "gross_receipts": round(gross),
        "presumed_income": round(presumed_income),
        "tax_before_cess": round(tax_before_cess),
        "health_education_cess_4pct": round(cess),
        "total_tax_liability": round(total_tax),
        "tds_already_deducted": round(tds),
        "tax_payable": round(payable),
        "refund_due": round(refund),
        "advance_tax_schedule": [
            {
                "due_by": "Jun 15",
                "percent": 15,
                "amount": round(payable * 0.15),
            },
            {
                "due_by": "Sep 15",
                "percent": 45,
                "amount": round(payable * 0.30),
            },
            {
                "due_by": "Dec 15",
                "percent": 75,
                "amount": round(payable * 0.30),
            },
            {
                "due_by": "Mar 15",
                "percent": 100,
                "amount": round(payable * 0.25),
            },
        ],
        "gst_registration_required": gross > 2000000,
        "regime": "New Tax Regime",
    }


# =========================
# MAIN RUN
# =========================
def run(worker_id: str):

    return {
        "agent": "TaxFilingAgent",
        "worker_id": worker_id,
        "itr4_prefill": compute_itr4(worker_id),
        "filing_status": "Ready to file",
    }