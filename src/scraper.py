"""Web scraping of publicly available financial information from the RBI website.

The Reserve Bank of India home page publishes its current policy rates, reserve
ratios and reference exchange rates as plain text. We download the page with
`requests`, strip the markup with BeautifulSoup, and pull each figure out with a
regular expression. If the site cannot be reached (no internet in the lab), the
app falls back to the last snapshot saved in data/rbi_rates.json.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

RBI_URL = "https://www.rbi.org.in/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/126.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-IN,en;q=0.9",
}
SNAPSHOT = Path(__file__).resolve().parent.parent / "data" / "rbi_rates.json"

# "Policy Repo Rate : 5.50%"  ->  ("Policy Repo Rate", "5.50")
RATE_RE = re.compile(
    r"(Policy Repo Rate|Standing Deposit Facility Rate|Marginal Standing Facility Rate|"
    r"Bank Rate|Fixed Reverse Repo Rate|CRR|SLR)\s*:\s*(\d+(?:\.\d+)?)\s*%"
)
# "INR / 1 USD : 92.9139"  ->  ("1 USD", "92.9139")
FX_RE = re.compile(r"INR\s*/\s*(\d+\s*[A-Z]{3})\s*:\s*(\d+(?:\.\d+)?)")

# Last known values (RBI home page, 27 Nov 2026) used only when offline.
FALLBACK = {
    "source": RBI_URL,
    "fetched_at": "2026-11-27 15:00",
    "live": False,
    "rates": {
        "Policy Repo Rate": 5.50,
        "Standing Deposit Facility Rate": 5.25,
        "Marginal Standing Facility Rate": 5.75,
        "Bank Rate": 5.75,
        "Fixed Reverse Repo Rate": 3.35,
        "CRR": 3.00,
        "SLR": 18.00,
    },
    "fx": {"1 USD": 92.9139, "1 GBP": 121.9563, "1 EUR": 102.0086},
}


def parse_rbi_text(text: str) -> dict:
    rates = {name: float(value) for name, value in RATE_RE.findall(text)}
    fx = {re.sub(r"\s+", " ", cur): float(value) for cur, value in FX_RE.findall(text)}
    return {"rates": rates, "fx": fx}


def fetch_rbi_rates(timeout: int = 8) -> dict:
    """Scrape live figures; on any failure return the saved snapshot."""
    try:
        import requests
        from bs4 import BeautifulSoup

        resp = requests.get(RBI_URL, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        text = BeautifulSoup(resp.text, "html.parser").get_text(" ", strip=True)
        parsed = parse_rbi_text(text)
        if not parsed["rates"]:
            raise ValueError("No rates found on page")
        result = {
            "source": RBI_URL,
            "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "live": True,
            **parsed,
        }
        SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
    except Exception as exc:  # network down, layout changed, blocked, etc.
        snap = load_snapshot()
        snap["error"] = f"{type(exc).__name__}: {exc}"[:160]
        return snap


def load_snapshot() -> dict:
    try:
        data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        data["live"] = False
        return data
    except (OSError, ValueError):
        return dict(FALLBACK)
