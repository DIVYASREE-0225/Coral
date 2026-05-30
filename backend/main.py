
"""GigProof FastAPI app."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agents import (
    credit,
    income_proof,
    ingestion,
    tax_filing,
    voice,
)

from logging_setup import (
    RequestIDMiddleware,
    configure as configure_logging,
)

from sql_engine import run_query

configure_logging()

app = FastAPI(
    title="GigProof API",
    version="0.1.0",
)

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestIDMiddleware)

# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).parent.resolve()
ASSETS_DIR = (BASE_DIR / "assets").resolve()
DATA_DIR = (BASE_DIR / "data").resolve()

# =========================
# VALIDATION
# =========================
_WORKER_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")


def _validate_worker_id(worker_id: str) -> str:
    if not _WORKER_ID_RE.fullmatch(worker_id):
        raise HTTPException(status_code=400, detail="Invalid worker_id")
    return worker_id


# =========================
# REQUEST MODELS
# =========================
class QueryRequest(BaseModel):
    sql: str


class VoiceRequest(BaseModel):
    worker_id: str
    question: str
    lang: str = "en"


# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {
        "name": "GigProof",
        "tagline": "Financial Identity Agent for India's Invisible Workforce",
        "status": "running",
    }


# =========================
# WORKERS
# =========================
@app.get("/workers")
def workers():

    path = DATA_DIR / "workers.csv"

    if not path.exists():
        raise HTTPException(
            status_code=500,
            detail="workers.csv not found",
        )

    df = pd.read_csv(path)

    return df.to_dict(orient="records")


# =========================
# SINGLE WORKER
# =========================
@app.get("/worker/{worker_id}")
async def worker_detail(worker_id: str):

    worker_id = _validate_worker_id(worker_id)

    path = DATA_DIR / "workers.csv"

    if not path.exists():
        raise HTTPException(
            status_code=500,
            detail="workers.csv not found",
        )

    df = pd.read_csv(path)

    rows = df[df["worker_id"] == worker_id]

    if rows.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Worker {worker_id} not found",
        )

    # =========================
    # SAFE EXECUTION
    # =========================

    try:
        ingestion_task = ingestion.run(worker_id)
    except Exception as e:
        ingestion_task = {
            "error": str(e)
        }

    try:
        tax_task = tax_filing.run(worker_id)
    except Exception as e:
        tax_task = {
            "error": str(e)
        }

    try:
        credit_task = credit.run(worker_id)
    except Exception as e:
        credit_task = {
            "error": str(e)
        }

    return {
        "profile": rows.iloc[0].to_dict(),
        "ingestion": ingestion_task,
        "tax": tax_task,
        "credit": credit_task,
    }


# =========================
# ITR
# =========================
@app.get("/itr/{worker_id}")
def itr(worker_id: str):

    worker_id = _validate_worker_id(worker_id)

    try:
        return tax_filing.run(worker_id)
    except Exception as e:
        return {
            "error": str(e)
        }


# =========================
# CREDIT SCORE
# =========================
@app.get("/credit/{worker_id}")
def credit_score(worker_id: str):

    worker_id = _validate_worker_id(worker_id)

    try:
        return credit.run(worker_id)
    except Exception as e:
        return {
            "error": str(e)
        }


# =========================
# INGESTION
# =========================
@app.get("/ingestion/{worker_id}")
def ingestion_view(worker_id: str):

    worker_id = _validate_worker_id(worker_id)

    try:
        return ingestion.run(worker_id)
    except Exception as e:
        return {
            "error": str(e)
        }


# =========================
# CERTIFICATE
# =========================
@app.post("/certificate/{worker_id}")
def certificate(worker_id: str):

    worker_id = _validate_worker_id(worker_id)

    try:
        return income_proof.run(worker_id)

    except Exception as e:
        return {
            "error": str(e)
        }


# =========================
# CERTIFICATE DOWNLOAD
# =========================
@app.get("/certificate/file/{filename}")
def certificate_file(filename: str):

    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename",
        )

    path = (ASSETS_DIR / filename).resolve()

    if ASSETS_DIR not in path.parents or not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Certificate not found",
        )

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=filename,
    )


# =========================
# VOICE AGENT
# =========================
@app.post("/voice")
def voice_query(req: VoiceRequest):

    try:
        return voice.run(
            _validate_worker_id(req.worker_id),
            req.question,
            req.lang,
        )

    except Exception as e:
        return {
            "error": str(e)
        }


# =========================
# SQL SCHEMAS
# =========================
@app.get("/sql/schemas")
def sql_schemas():

    return [
        {
            "table": "workers",
            "columns": [
                {"name": "worker_id", "type": "string"},
                {"name": "name", "type": "string"},
                {"name": "city", "type": "string"},
                {"name": "language", "type": "string"},
                {"name": "phone", "type": "string"},
                {"name": "pan", "type": "string"},
                {"name": "platforms", "type": "string"},
            ],
        },
        {
            "table": "income_ledger",
            "columns": [
                {"name": "worker_id", "type": "string"},
                {"name": "platform", "type": "string"},
                {"name": "amount", "type": "number"},
                {"name": "earned_on", "type": "date"},
                {"name": "tds_deducted", "type": "number"},
            ],
        },
    ]


# =========================
# SQL EXAMPLES
# =========================
@app.get("/sql/examples")
def sql_examples():

    return [
        {
            "name": "All Workers",
            "sql": "SELECT * FROM workers",
        },
        {
            "name": "Worker Income",
            "sql": """
SELECT worker_id, SUM(amount) AS total_income
FROM income_ledger
GROUP BY worker_id
            """,
        },
        {
            "name": "Platform Revenue",
            "sql": """
SELECT platform, SUM(amount) AS revenue
FROM income_ledger
GROUP BY platform
            """,
        },
    ]


# =========================
# SQL ORCHESTRATION
# =========================
@app.post("/sql/query")
def sql_query(req: QueryRequest):

    try:

        rows = run_query(req.sql)

        return {
            "success": True,
            "rows": rows,
            "row_count": len(rows),
        }

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

