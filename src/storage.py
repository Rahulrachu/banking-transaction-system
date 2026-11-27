"""Storage: CSV / JSON / text / binary (pickle) (Group 4 requirement)."""

from __future__ import annotations

import pickle
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent / "data"
BASE.mkdir(parents=True, exist_ok=True)


def save_all(df: pd.DataFrame, stem: str = "transactions") -> dict:
    csv_path = BASE / f"{stem}.csv"
    json_path = BASE / f"{stem}.json"
    txt_path = BASE / f"{stem}.txt"
    bin_path = BASE / f"{stem}.bin"

    df.to_csv(csv_path, index=False)
    df.to_json(json_path, orient="records", indent=2)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("Banking Transaction & Financial Analysis — Report\n")
        f.write(f"Rows: {len(df)}\n")
        f.write(df.to_string(index=False))

    with open(bin_path, "wb") as f:
        pickle.dump(df, f)

    return {
        "csv": str(csv_path),
        "json": str(json_path),
        "txt": str(txt_path),
        "bin": str(bin_path),
    }


def save_accounts(accounts: list[dict]) -> dict:
    df = pd.DataFrame(accounts)
    return save_all(df, stem="accounts")


def load_csv(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)


def export_statement(account_no: str, customer: str, txns: list[dict]) -> str:
    """Generate a text account statement (extra feature / reporting)."""
    lines = [
        "=== Account Statement (demo) ===",
        f"Customer: {customer}  |  Account: {account_no}",
        "",
    ]
    running = 0.0
    for t in txns:
        signed = float(t["amount"]) if t["type"] in ("deposit", "transfer_in") else -float(t["amount"])
        running += signed
        lines.append(
            f"{t['date']}  {t['txn_ref']:<16} {t['type']:<13} ₹{signed:>10,.2f}  bal ₹{running:>10,.2f}  {t['counterparty']}"
        )
    lines.append("")
    lines.append(f"Closing net (this statement): ₹{running:,.2f}")
    return "\n".join(lines)
