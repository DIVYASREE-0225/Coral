# GigProof — Financial Identity Agent for India's Invisible Workforce

Multi-agent system on Coral that ingests gig earnings across Zomato, Swiggy, Ola, Uber, auto-files ITR, generates a bank-grade income certificate, and builds a credit identity — all from a single SQL query, in any language.

## Stack

- **Backend**: Python 3.11+, FastAPI, DuckDB (Coral SQL engine), ReportLab (PDF), qrcode
- **Frontend**: Next.js 14, Tailwind CSS, Recharts
- **Coral**: 6 agents orchestrated via SQL-like cross-source queries

## Quickstart

### Backend (Python 3.11+, recommended 3.13)
```bash
cd backend
python3.13 -m venv .coralvenv
source .coralvenv/bin/activate
pip install fastapi 'uvicorn[standard]' duckdb pandas reportlab 'qrcode[pil]' pydantic python-multipart
python seed.py                                  # generates 12 months of mock data
uvicorn main:app --reload --port 8000
```

### Frontend (Node 18+)
```bash
cd frontend
npm install
npm run dev                                     # http://localhost:3000
```

### Demo path
1. Open <http://localhost:3000> — pick a worker.
2. Worker dashboard: see unified income ledger, ITR-4 pre-fill, gig credit score.
3. Click **Generate certificate** — downloads a signed PDF with QR.
4. Try the multilingual voice agent at the bottom.
5. Hit **SQL Playground** for the cross-source query demo (Coral's superpower).

## The Six Agents

| Agent | Role |
|---|---|
| Platform Ingestion | Pulls Zomato/Swiggy/Ola/Uber payouts → unified income ledger |
| Tax Filing | 44ADA/44AD calc, advance tax schedule, ITR-4 pre-fill |
| Income Proof Generator | Signed PDF certificate with QR (bank-accepted) |
| Credit Score Builder | Income consistency + tenure + growth → gig-native score |
| Multilingual Voice | Hindi / Telugu / Tamil / Kannada via WhatsApp |
| SQL Orchestrator | Cross-source SQL across all agents — Coral's superpower |

## Demo Workers

- `W001` — Ravi (Hyderabad, Zomato + Swiggy delivery, ₹32K/mo)
- `W002` — Priya (Bangalore, Urban Company beautician, ₹45K/mo)
- `W003` — Arjun (Mumbai, Ola + Uber driver, ₹38K/mo)
