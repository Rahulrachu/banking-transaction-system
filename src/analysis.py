"""Daily, monthly and yearly transaction statistics with NumPy and Pandas."""

from __future__ import annotations

import numpy as np
import pandas as pd

CREDIT_TYPES = ("deposit", "transfer_in")
COLUMNS = ["txn_ref", "account_no", "customer", "type", "counterparty", "amount",
           "timestamp", "channel", "balance_after"]


def to_dataframe(transactions: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(transactions, columns=COLUMNS)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["is_credit"] = df["type"].isin(CREDIT_TYPES)
    df["signed"] = np.where(df["is_credit"], df["amount"], -df["amount"])
    df["credit"] = np.where(df["is_credit"], df["amount"], 0.0)
    df["debit"] = np.where(df["is_credit"], 0.0, df["amount"])
    df["date"] = df["timestamp"].dt.normalize()
    df["month"] = df["timestamp"].dt.to_period("M").astype(str)
    df["year"] = df["timestamp"].dt.year
    return df


def _period_stats(df: pd.DataFrame, key: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[key, "transactions", "money_in", "money_out", "net", "average", "largest"])
    g = df.groupby(key)
    out = pd.DataFrame({
        "transactions": g.size(),
        "money_in": g["credit"].sum(),
        "money_out": g["debit"].sum(),
        "net": g["signed"].sum(),
        "average": g["amount"].mean(),
        "largest": g["amount"].max(),
    }).round(2).reset_index()
    return out.sort_values(key)


def daily_stats(df: pd.DataFrame) -> pd.DataFrame:
    return _period_stats(df, "date")


def monthly_stats(df: pd.DataFrame) -> pd.DataFrame:
    out = _period_stats(df, "month")
    if not out.empty:
        # month-over-month change in spending, as a percentage
        out["spend_change_pct"] = (out["money_out"].pct_change() * 100).round(1)
    return out


def yearly_stats(df: pd.DataFrame) -> pd.DataFrame:
    return _period_stats(df, "year")


def summary_numbers(df: pd.DataFrame) -> dict:
    """Headline statistics computed with NumPy."""
    amounts = df["amount"].to_numpy()
    if amounts.size == 0:
        return {"count": 0, "mean": 0, "median": 0, "std": 0, "p95": 0, "total_in": 0, "total_out": 0}
    return {
        "count": int(amounts.size),
        "mean": float(np.mean(amounts)),
        "median": float(np.median(amounts)),
        "std": float(np.std(amounts)),
        "p95": float(np.percentile(amounts, 95)),
        "total_in": float(df["credit"].sum()),
        "total_out": float(df["debit"].sum()),
    }


def spending_by_category(df: pd.DataFrame) -> pd.DataFrame:
    spend = df[df["type"] == "withdrawal"]
    if spend.empty:
        return pd.DataFrame(columns=["category", "amount", "transactions", "share_pct"])
    g = spend.groupby("counterparty")["amount"]
    out = pd.DataFrame({"amount": g.sum(), "transactions": g.size()}).reset_index()
    out = out.rename(columns={"counterparty": "category"})
    out["share_pct"] = (100 * out["amount"] / out["amount"].sum()).round(1)
    return out.sort_values("amount", ascending=False).round(2)


def channel_mix(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["channel", "transactions", "amount"])
    g = df.groupby("channel")["amount"]
    return pd.DataFrame({"transactions": g.size(), "amount": g.sum().round(2)}).reset_index() \
        .sort_values("transactions", ascending=False)


def hourly_heat(df: pd.DataFrame) -> pd.DataFrame:
    """Transactions by weekday and hour, for the activity heatmap."""
    if df.empty:
        return pd.DataFrame()
    t = df.assign(weekday=df["timestamp"].dt.day_name().str[:3], hour=df["timestamp"].dt.hour)
    order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    pivot = t.pivot_table(index="weekday", columns="hour", values="txn_ref", aggfunc="count", fill_value=0)
    return pivot.reindex(order).reindex(columns=range(24), fill_value=0).fillna(0).astype(int)


def account_summary(df: pd.DataFrame, accounts: list[dict]) -> pd.DataFrame:
    acc = pd.DataFrame(accounts)[["account_no", "name", "branch", "balance"]]
    if df.empty:
        acc["transactions"] = 0
        return acc
    g = df.groupby("account_no")
    stats = pd.DataFrame({
        "transactions": g.size(),
        "money_in": g["credit"].sum().round(2),
        "money_out": g["debit"].sum().round(2),
    }).reset_index()
    return acc.merge(stats, on="account_no", how="left").fillna(0)
