import pandas as pd
from pathlib import Path

data_dir = Path("backend/data")

files = [
    "zomato_payouts",
    "swiggy_payouts",
    "ola_settlements",
    "uber_statements",
    "urbancompany_jobs",
    "workers"
]

for name in files:
    csv_path = data_dir / f"{name}.csv"
    jsonl_path = data_dir / f"{name}.jsonl"

    df = pd.read_csv(csv_path)

    df.to_json(
        jsonl_path,
        orient="records",
        lines=True
    )

    print(f"Created: {jsonl_path}")