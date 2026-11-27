"""Monthly money insights and savings-goal projection for one customer."""

from __future__ import annotations

import numpy as np
import pandas as pd


def monthly_insights(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["month", "income", "spend", "net", "savings_rate_pct", "top_spend"])
    rows = []
    for month, grp in df.groupby("month"):
        income = float(grp["credit"].sum())
        spend = float(grp["debit"].sum())
        spends = grp[grp["type"] == "withdrawal"]
        rows.append({
            "month": month,
            "income": round(income, 2),
            "spend": round(spend, 2),
            "net": round(income - spend, 2),
            "savings_rate_pct": round(100 * (income - spend) / income, 1) if income else 0.0,
            "top_spend": spends.groupby("counterparty")["amount"].sum().idxmax() if len(spends) else "-",
        })
    return pd.DataFrame(rows).sort_values("month")


def goal_projection(balance: float, monthly_save: float, months: int, annual_rate_pct: float) -> pd.DataFrame:
    r = annual_rate_pct / 100 / 12
    k = np.arange(1, int(months) + 1)
    growth = (1 + r) ** k
    saved = balance * growth + (monthly_save * (growth - 1) / r if r else monthly_save * k)
    return pd.DataFrame({"month": k, "balance": np.round(saved, 2)})
