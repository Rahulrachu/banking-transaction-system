"""EXTRA FEATURE 1 — Monthly money insights (cashflow, savings rate, top spends)."""

from __future__ import annotations

import pandas as pd


def monthly_insights(df: pd.DataFrame) -> pd.DataFrame:
    """Per-month: income, spend, net, savings rate %, top counterparty."""
    if df.empty:
        return pd.DataFrame(columns=["month", "income", "spend", "net", "savings_rate_pct", "top_spend"])
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)
    rows = []
    for month, grp in df.groupby("month"):
        income = float(grp.loc[grp["type"].isin(["deposit", "transfer_in"]), "amount"].sum())
        spend = float(grp.loc[grp["type"].isin(["withdrawal", "transfer_out"]), "amount"].sum())
        net = income - spend
        rate = round(100 * net / income, 1) if income else 0.0
        spends = grp[grp["type"].isin(["withdrawal", "transfer_out"])]
        top = (
            spends.groupby("counterparty")["amount"].sum().idxmax()
            if not spends.empty
            else "—"
        )
        rows.append(
            {
                "month": month,
                "income": round(income, 2),
                "spend": round(spend, 2),
                "net": round(net, 2),
                "savings_rate_pct": rate,
                "top_spend": top,
            }
        )
    return pd.DataFrame(rows).sort_values("month")


def goal_projection(balance: float, monthly_save: float, months: int, annual_rate_pct: float = 6.0) -> list[dict]:
    """Simple monthly compounding projection for a savings goal."""
    balance = float(balance or 0)
    monthly_save = float(monthly_save or 0)
    r = float(annual_rate_pct or 0) / 100 / 12
    points, bal = [], balance
    for m in range(1, int(months or 0) + 1):
        bal = bal * (1 + r) + monthly_save
        points.append({"month": m, "balance": round(bal, 2)})
    return points
