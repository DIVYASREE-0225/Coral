"""Multilingual Voice Agent.

Translates structured agent output into vernacular voice replies
(Telugu / Hindi / Tamil / Kannada). For the demo, we use canned templates
that interpolate live data — production would route through Bhashini/Whisper
for ASR and a TTS backend for response audio.

Intent → handler. Each handler returns text in the requested language.
"""
from __future__ import annotations

from agents import credit, ingestion, tax_filing
from coral_sql import query

LANGS = ["en", "hi", "te", "ta", "kn"]


def _worker_name(worker_id: str) -> str:
    rows = query(f"SELECT name FROM gigproof.workers WHERE worker_id = '{worker_id}'")
    return rows[0]["name"] if rows else worker_id


def _last_month_total(worker_id: str) -> int:
    rows = query(f"""
        SELECT SUM(amount) AS total
        FROM income_ledger
        WHERE worker_id = '{worker_id}'
          AND earned_on >= (SELECT MAX(earned_on) FROM income_ledger WHERE worker_id = '{worker_id}') - INTERVAL 30 DAY
    """)
    return int(rows[0]["total"] or 0) if rows else 0


def _detect_intent(question: str) -> str:
    q = question.lower()
    if any(k in q for k in ["earn", "income", "salary", "kamai", "kamaai", "enti", "paisa"]):
        return "earnings"
    if any(k in q for k in ["tax", "itr", "file"]):
        return "tax"
    if any(k in q for k in ["loan", "credit", "score", "cibil"]):
        return "credit"
    if any(k in q for k in ["certificate", "proof", "slip"]):
        return "certificate"
    return "summary"


def _earnings_response(worker_id: str, lang: str) -> str:
    name = _worker_name(worker_id)
    total = _last_month_total(worker_id)
    by_platform = ingestion.platform_breakdown(worker_id)
    platforms = ", ".join(p["platform"] for p in by_platform)

    if lang == "te":
        return f"{name} garu, mee gata 30 rojulalo motham sampaadana ₹{total:,}. {platforms} platforms nundi vasthondi."
    if lang == "hi":
        return f"{name} ji, pichhle 30 din mein aapki kul kamai ₹{total:,} hai. Yeh {platforms} se aayi hai."
    if lang == "ta":
        return f"{name}, kadanda 30 naatkalil ungal mottha varumanam ₹{total:,}. {platforms} thalangaliruntu kidaithathu."
    if lang == "kn":
        return f"{name}, kaledha 30 dinagalalli nimma othu sampadane ₹{total:,}. {platforms} platforms inda."
    return f"{name}, your total earnings in the last 30 days were ₹{total:,} across {platforms}."


def _tax_response(worker_id: str, lang: str) -> str:
    itr = tax_filing.compute_itr4(worker_id)
    payable = itr["tax_payable"]
    if lang == "hi":
        return f"Aapki ITR-4 taiyaar hai. Kul tax payable ₹{payable:,}. Hum aapke liye file kar sakte hain — bas haan boliye."
    if lang == "te":
        return f"Mee ITR-4 ready ga undi. Tax payable ₹{payable:,}. Memu file cheyyamaa? Avunani cheppandi."
    if lang == "ta":
        return f"Ungal ITR-4 thayaaraga ullathu. Sellavendiya tax ₹{payable:,}. Naangal file panna mudiyuma?"
    return f"Your ITR-4 is ready. Tax payable: ₹{payable:,}. Want us to file it for you?"


def _credit_response(worker_id: str, lang: str) -> str:
    cs = credit.compute_score(worker_id)
    score, verdict = cs["score"], cs["verdict"]
    if lang == "hi":
        return f"Aapka GigProof credit score {score} hai. {verdict}"
    if lang == "te":
        return f"Mee GigProof credit score {score}. {verdict}"
    if lang == "ta":
        return f"Ungal GigProof credit score {score}. {verdict}"
    return f"Your GigProof credit score is {score}. {verdict}"


def _certificate_response(worker_id: str, lang: str) -> str:
    if lang == "hi":
        return "Aapka Digital Employment & Income Certificate WhatsApp pe bhej diya. QR code se bank verify kar sakta hai."
    if lang == "te":
        return "Mee Digital Income Certificate WhatsApp ki vacchindi. Bank QR code tho verify cheyagaladu."
    return "Your Digital Income Certificate has been sent to WhatsApp. The bank can verify it via the QR code."


def answer(worker_id: str, question: str, lang: str = "en") -> dict:
    if lang not in LANGS:
        lang = "en"
    intent = _detect_intent(question)
    if intent == "earnings":
        text = _earnings_response(worker_id, lang)
    elif intent == "tax":
        text = _tax_response(worker_id, lang)
    elif intent == "credit":
        text = _credit_response(worker_id, lang)
    elif intent == "certificate":
        text = _certificate_response(worker_id, lang)
    else:
        text = _earnings_response(worker_id, lang)

    return {"intent": intent, "language": lang, "response": text, "channel": "WhatsApp Voice"}


def run(worker_id: str, question: str = "naa last month earnings enti?", lang: str = "te") -> dict:
    return {"agent": "MultilingualVoiceAgent", "worker_id": worker_id, **answer(worker_id, question, lang)}
