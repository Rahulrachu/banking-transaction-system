"""Web scraping — permitted public financial info with safe fallback.

Tries light scraping of permitted pages (RBI / data.gov.in index pages).
Parses % / Rs figures with regex. Falls back to a realistic seeded sample
so the demo always runs offline. Educational use only.
"""

from __future__ import annotations

import re
import random
from datetime import date, timedelta

PCT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")
RS_RE = re.compile(r"(?:Rs\.?|₹)\s*([\d,]+\.?\d*)", re.IGNORECASE)

PERMITTED_URLS = [
    "https://www.rbi.org.in/",
    "https://www.data.gov.in/",
]
HEADERS = {"User-Agent": "Mozilla/5.0 (Student Project; Educational Use)"}

# Seeded demo customers (10-digit account numbers, PAN-format placeholders)
SAMPLE_CUSTOMERS = [
    {"name": "Rahul S R", "account_no": "2601299501", "pan": "BCCCC1234F", "phone": "9019709994", "balance": 84500.0, "branch": "Jayanagar"},
    {"name": "P Kavi Arasu", "account_no": "2601298902", "pan": "BCCCC1234F", "phone": "9886012345", "balance": 52300.0, "branch": "Jayanagar"},
    {"name": "Prachodna B", "account_no": "2601299003", "pan": "BCCCC1234F", "phone": "9620011223", "balance": 127800.0, "branch": "Koramangala"},
    {"name": "Sarvesh MT", "account_no": "2601301204", "pan": "BCCCC1234F", "phone": "9742011223", "balance": 31900.0, "branch": "Malleshwaram"},
    {"name": "Asha Rao", "account_no": "2601315505", "pan": "BCCCC1234F", "phone": "9986012345", "balance": 210400.0, "branch": "HSR Layout"},
    {"name": "Vikram Patil", "account_no": "2601315506", "pan": "BCCCC1234F", "phone": "9885012345", "balance": 47600.0, "branch": "Whitefield"},
]

TXN_TYPES = ["deposit", "withdrawal", "transfer_out", "transfer_in"]
COUNTERPARTIES = ["UPI-Merchant", "Electricity Bill", "Salary Credit", "ATM", "Online Cart", "Rent Transfer", "FD Interest"]


def scrape_live(timeout: int = 5) -> dict:
    """Try scraping permitted pages. Returns {ok, url, pcts, raw_chars}."""
    try:
        import requests

        for url in PERMITTED_URLS:
            try:
                resp = requests.get(url, headers=HEADERS, timeout=timeout)
                resp.raise_for_status()
                pcts = PCT_RE.findall(resp.text[:200_000])
                return {"ok": bool(pcts), "url": url, "pcts": pcts[:10], "raw_chars": len(resp.text)}
            except Exception:
                continue
    except Exception:
        pass
    return {"ok": False, "url": None, "pcts": [], "raw_chars": 0}


def generate_transactions(seed: int = 42, n: int = 120) -> list[dict]:
    """Generate n realistic transactions over the last 60 days (seeded)."""
    from src.validation import generate_txn_ref

    rng = random.Random(seed)
    today = date.today()
    txns: list[dict] = []
    for i in range(n):
        cust = rng.choice(SAMPLE_CUSTOMERS)
        days_ago = rng.randint(0, 59)
        d = today - timedelta(days=days_ago)
        ttype = rng.choices(TXN_TYPES, weights=[3, 4, 2, 2], k=1)[0]
        # amounts: small daily + rare large (for fraud demo)
        if rng.random() < 0.06:
            amount = round(rng.uniform(75000, 250000), 2)
        else:
            amount = round(rng.uniform(200, 25000), 2)
        txns.append(
            {
                "txn_ref": generate_txn_ref(seed=f"{cust['account_no']}{i}{d}"),
                "account_no": cust["account_no"],
                "customer": cust["name"],
                "type": ttype,
                "counterparty": rng.choice(COUNTERPARTIES),
                "amount": amount,
                "date": d.isoformat(),
                "channel": rng.choice(["UPI", "Card", "NetBanking", "Branch", "ATM"]),
            }
        )
    txns.sort(key=lambda t: t["date"])
    return txns
