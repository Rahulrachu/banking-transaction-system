"""Suspicious transaction detection (Group 4 core requirement).

Rules (transparent, auditable):
1. Large single transaction above a threshold (default ₹50,000).
2. Burst: 3+ transactions for one account within 24 hours.
3. Odd-hour activity (00:00–04:00) flagged for review.
"""

from __future__ import annotations

from collections import Counter
import pandas as pd


def flag_suspicious(df: pd.DataFrame, large_threshold: float = 50_000) -> pd.DataFrame:
    """Return flagged transactions with reasons."""
    if df.empty:
        return pd.DataFrame(columns=["txn_ref", "account_no", "customer", "type", "amount", "date", "reasons"])
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["day"] = df["date"].dt.date

    # burst rule: count per account per day
    counts = df.groupby(["account_no", "day"])["txn_ref"].transform("count")
    df["is_large"] = df["amount"] >= large_threshold
    df["is_burst"] = counts >= 3
    df["is_night"] = df["date"].dt.hour < 4

    flagged = df[df["is_large"] | df["is_burst"]].copy()

    def reasons(row) -> str:
        bits = []
        if row["is_large"]:
            bits.append(f"Large ≥ ₹{large_threshold:,.0f}")
        if row["is_burst"]:
            bits.append(f"Burst ({counts.loc[row.name]} txns/day)")
        if row["is_night"]:
            bits.append("Night hours")
        return "; ".join(bits)

    if flagged.empty:
        return pd.DataFrame(columns=["txn_ref", "account_no", "customer", "type", "amount", "date", "reasons"])
    flagged["reasons"] = flagged.apply(reasons, axis=1)
    cols = ["txn_ref", "account_no", "customer", "type", "amount", "date", "reasons"]
    return flagged[cols].sort_values("date", ascending=False)


def fraud_summary(df: pd.DataFrame) -> dict:
    flagged = flag_suspicious(df)
    total = len(df)
    return {
        "flagged": len(flagged),
        "total": total,
        "rate_pct": round(100 * len(flagged) / total, 2) if total else 0.0,
        "by_customer": flagged["customer"].value_counts().to_dict() if not flagged.empty else {},
    }
