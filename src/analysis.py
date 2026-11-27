"""Daily / monthly / yearly analysis with NumPy + Pandas (Group 4 requirement)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def to_dataframe(transactions: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(transactions)
    if df.empty:
        return pd.DataFrame(
            columns=["txn_ref", "account_no", "customer", "type", "counterparty", "amount", "date", "channel"]
        )
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["signed"] = np.where(df["type"].isin(["deposit", "transfer_in"]), df["amount"], -df["amount"])
    return df


def daily_stats(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["date", "txn_count", "total_in", "total_out", "net"])
    df = df.copy()
    df["day"] = df["date"].dt.date
    g = df.groupby("day")
    out = pd.DataFrame(
        {
            "txn_count": g.size(),
            "total_in": g.apply(lambda x: x.loc[x["signed"] > 0, "amount"].sum(), include_groups=False).round(2),
            "total_out": g.apply(lambda x: x.loc[x["signed"] < 0, "amount"].sum(), include_groups=False).round(2),
            "net": g["signed"].sum().round(2),
        }
    ).reset_index()
    return out.sort_values("day")


def monthly_stats(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["month", "txn_count", "total_in", "total_out", "net", "avg_txn"])
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M").astype(str)
    g = df.groupby("month")
    out = pd.DataFrame(
        {
            "txn_count": g.size(),
            "total_in": g.apply(lambda x: x.loc[x["signed"] > 0, "amount"].sum(), include_groups=False).round(2),
            "total_out": g.apply(lambda x: x.loc[x["signed"] < 0, "amount"].sum(), include_groups=False).round(2),
            "net": g["signed"].sum().round(2),
            "avg_txn": g["amount"].mean().round(2),
        }
    ).reset_index()
    return out.sort_values("month")


def yearly_stats(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["year", "txn_count", "net"])
    df = df.copy()
    df["year"] = df["date"].dt.year.astype(str)
    g = df.groupby("year")
    out = pd.DataFrame({"txn_count": g.size(), "net": g["signed"].sum().round(2)}).reset_index()
    return out.sort_values("year")


def account_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["customer", "account_no", "txn_count", "net_flows"])
    g = df.groupby(["customer", "account_no"])
    out = pd.DataFrame(
        {"txn_count": g.size(), "net_flows": g["signed"].sum().round(2), "total_volume": g["amount"].sum().round(2)}
    ).reset_index()
    return out.sort_values("total_volume", ascending=False)


def spending_by_counterparty(df: pd.DataFrame) -> pd.DataFrame:
    """Where money goes (outflows only) — NumPy percentile band included."""
    out_df = df[df["signed"] < 0] if not df.empty else df
    if out_df.empty:
        return pd.DataFrame(columns=["counterparty", "spend", "txns", "p75"])
    g = out_df.groupby("counterparty")["amount"]
    out = pd.DataFrame(
        {"spend": g.sum().round(2), "txns": g.count(), "p75": g.quantile(0.75).round(2)}
    ).reset_index()
    return out.sort_values("spend", ascending=False)
