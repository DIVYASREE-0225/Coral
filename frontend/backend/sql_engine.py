import duckdb
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"


def run_query(sql: str):

    conn = duckdb.connect()

    # workers
    workers = pd.read_csv(DATA_DIR / "workers.csv")
    conn.register("workers", workers)

    # income ledger
    ledger_path = DATA_DIR / "income_ledger.csv"

    if ledger_path.exists():
        ledger = pd.read_csv(ledger_path)
    else:
        ledger = pd.DataFrame(
            columns=[
                "worker_id",
                "platform",
                "amount",
                "earned_on",
                "tds_deducted",
            ]
        )

    conn.register("income_ledger", ledger)

    result = conn.execute(sql).fetchdf()

    return result.to_dict(orient="records")