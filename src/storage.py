"""File storage (CSV, JSON, text, binary) plus account statements and reports."""

from __future__ import annotations

import json
import pickle
from datetime import datetime
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class StorageError(Exception):
    pass


def save_all(transactions: list[dict], accounts: list[dict]) -> dict[str, str]:
    """Write transactions and accounts in all four formats. Returns the file paths."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        tx = pd.DataFrame(transactions)
        paths = {
            "CSV": DATA_DIR / "transactions.csv",
            "JSON": DATA_DIR / "accounts.json",
            "Text": DATA_DIR / "transactions.txt",
            "Binary": DATA_DIR / "bank_snapshot.pkl",
        }
        tx.to_csv(paths["CSV"], index=False)
        paths["JSON"].write_text(json.dumps(accounts, indent=2), encoding="utf-8")
        with open(paths["Text"], "w", encoding="utf-8") as fh:
            fh.write(f"Transaction log · generated {datetime.now():%d %b %Y %H:%M}\n\n")
            fh.write(tx.to_string(index=False))
        with open(paths["Binary"], "wb") as fh:
            pickle.dump({"accounts": accounts, "transactions": transactions}, fh)
        return {k: str(v.relative_to(DATA_DIR.parent)) for k, v in paths.items()}
    except (OSError, pickle.PickleError) as exc:
        raise StorageError(f"Could not save files: {exc}") from exc


def load_snapshot() -> dict | None:
    path = DATA_DIR / "bank_snapshot.pkl"
    try:
        with open(path, "rb") as fh:
            return pickle.load(fh)
    except FileNotFoundError:
        return None
    except (OSError, pickle.UnpicklingError, EOFError) as exc:
        raise StorageError(f"Snapshot is unreadable: {exc}") from exc


def statement_text(account: dict, txns: list[dict], start: str, end: str) -> str:
    """Plain-text bank statement with opening and closing balance for a date range."""
    rows = sorted((t for t in txns if start <= t["timestamp"][:10] <= end), key=lambda t: t["timestamp"])
    before = [t for t in sorted(txns, key=lambda t: t["timestamp"]) if t["timestamp"][:10] < start]
    opening = before[-1]["balance_after"] if before else account["opening_balance"]
    credit = sum(t["amount"] for t in rows if t["type"] in ("deposit", "transfer_in"))
    debit = sum(t["amount"] for t in rows if t["type"] not in ("deposit", "transfer_in"))
    w = 98
    out = [
        "ACCOUNT STATEMENT".center(w),
        "Group 4 Bank · Python Activity 3".center(w),
        "=" * w,
        f"Name    : {account['name']:<34}Account : {account['account_no']}",
        f"Branch  : {account['branch']:<34}Period  : {start} to {end}",
        "-" * w,
        f"{'Date':<17}{'Reference':<16}{'Description':<29}{'Debit':>12}{'Credit':>12}{'Balance':>12}",
        "-" * w,
        f"{'':<17}{'':<16}{'Opening balance':<29}{'':>12}{'':>12}{opening:>12,.2f}",
    ]
    for t in rows:
        is_cr = t["type"] in ("deposit", "transfer_in")
        amt = f"{t['amount']:,.2f}"
        dr, cr = ("", amt) if is_cr else (amt, "")
        when = t["timestamp"][:16].replace("T", " ")
        out.append(
            f"{when:<17}{t['txn_ref']:<16}{t['counterparty'][:28]:<29}{dr:>12}{cr:>12}{t['balance_after']:>12,.2f}"
        )
    closing = rows[-1]["balance_after"] if rows else opening
    out += [
        "-" * w,
        f"Total debits : Rs {debit:,.2f}    Total credits : Rs {credit:,.2f}    Closing balance : Rs {closing:,.2f}",
        f"Transactions : {len(rows)}",
        "=" * w,
        f"Generated {datetime.now():%d %b %Y %H:%M}. Computer-generated statement.",
    ]
    return "\n".join(out)


def statement_csv(txns: list[dict], start: str, end: str) -> str:
    rows = [t for t in txns if start <= t["timestamp"][:10] <= end]
    return pd.DataFrame(rows).to_csv(index=False)


def financial_report(monthly: pd.DataFrame, yearly: pd.DataFrame, summary: dict,
                     flagged_count: int, total_balance: float) -> str:
    lines = [
        "FINANCIAL REPORT",
        f"Generated {datetime.now():%d %b %Y %H:%M}",
        "",
        f"Total deposits held     : Rs {total_balance:,.2f}",
        f"Transactions analysed   : {summary['count']}",
        f"Money in / out          : Rs {summary['total_in']:,.2f} / Rs {summary['total_out']:,.2f}",
        f"Average transaction     : Rs {summary['mean']:,.2f} (median Rs {summary['median']:,.2f})",
        f"95th percentile amount  : Rs {summary['p95']:,.2f}",
        f"Flagged for review      : {flagged_count}",
        "",
        "YEARLY",
        yearly.to_string(index=False),
        "",
        "MONTHLY",
        monthly.to_string(index=False),
    ]
    return "\n".join(lines)
