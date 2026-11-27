"""Suspicious-transaction detection.

Rule-based checks (transparent and easy to explain):
  R1 Large amount     - a single debit at or above the threshold
  R2 Burst            - 4 or more debits from one account on the same day
  R3 Odd hours        - activity between 00:00 and 04:00
  R4 Rapid drain      - one debit takes more than 70% of the balance before it

Pattern-based check (Extra feature 1, see risk.py):
  Each transaction also gets a 0-100 risk score from a NumPy z-score of the
  amount against that customer's own history.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.risk import add_risk_scores

DEBIT_TYPES = ("withdrawal", "transfer_out")


def flag_suspicious(df: pd.DataFrame, large_threshold: float = 50_000.0) -> pd.DataFrame:
    if df.empty:
        return df.assign(reasons=pd.Series(dtype=str), rules=pd.Series(dtype=int))
    d = add_risk_scores(df)
    debit = d["type"].isin(DEBIT_TYPES)

    d["r_large"] = debit & (d["amount"] >= large_threshold)
    per_day = d[debit].groupby(["account_no", "date"])["txn_ref"].transform("count")
    d["r_burst"] = False
    d.loc[per_day.index, "r_burst"] = per_day >= 4
    d["r_night"] = d["timestamp"].dt.hour < 4
    before = d["balance_after"] + d["amount"]
    d["r_drain"] = debit & (d["amount"] > 0.7 * before)

    labels = {
        "r_large": f"Large debit (Rs {large_threshold:,.0f}+)",
        "r_burst": "4+ debits in one day",
        "r_night": "Between 00:00 and 04:00",
        "r_drain": "Took over 70% of balance",
    }
    flags = d[list(labels)].to_numpy()
    d["rules"] = flags.sum(axis=1)
    d["reasons"] = [" · ".join(labels[k] for k, hit in zip(labels, row) if hit) for row in flags]
    flagged = d[(d["rules"] > 0) | (d["risk_level"] == "High")].copy()
    flagged.loc[flagged["reasons"] == "", "reasons"] = "Unusual for this customer"
    return flagged.sort_values(["risk_score", "timestamp"], ascending=False)


def fraud_summary(flagged: pd.DataFrame, total: int) -> dict:
    return {
        "flagged": int(len(flagged)),
        "high": int((flagged.get("risk_level") == "High").sum()) if len(flagged) else 0,
        "rate_pct": round(100 * len(flagged) / total, 2) if total else 0.0,
        "by_customer": flagged["customer"].value_counts().to_dict() if len(flagged) else {},
        "total_amount": float(np.round(flagged["amount"].sum(), 2)) if len(flagged) else 0.0,
    }
