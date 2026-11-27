"""EXTRA FEATURE 1 - Smart risk score (statistical anomaly detection with NumPy).

A fixed threshold treats Rs 60,000 the same for everyone, but that amount is
normal for a high earner and alarming for a student. Here every transaction is
compared with the same customer's own history:

    z = (amount - customer mean) / customer standard deviation

The z-score, the time of day and the channel are combined into a 0-100 score:
    Low < 40 <= Medium < 70 <= High
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_risk_scores(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    if d.empty:
        return d.assign(z_score=[], risk_score=[], risk_level=[])
    grp = d.groupby("account_no")["amount"]
    mean = grp.transform("mean").to_numpy()
    std = grp.transform("std").fillna(0).to_numpy()
    amount = d["amount"].to_numpy()
    z = np.divide(amount - mean, std, out=np.zeros_like(amount), where=std > 0)
    hour = d["timestamp"].dt.hour.to_numpy()
    is_debit = d["type"].isin(["withdrawal", "transfer_out"]).to_numpy()


    score = np.clip(z, 0, None) * np.where(is_debit, 18, 4)  # unusually large debit for this person
    score += np.where((hour < 4), 25, 0)                   # odd hours
    score += np.where(is_debit, 8, 0)                      # money leaving the account
    score += np.where(d["channel"].eq("ATM").to_numpy() & (hour < 5), 10, 0)
    score = np.clip(np.round(score), 0, 100)

    d["z_score"] = np.round(z, 2)
    d["risk_score"] = score.astype(int)
    d["risk_level"] = np.select([score >= 70, score >= 40], ["High", "Medium"], default="Low")
    return d


def risk_distribution(scored: pd.DataFrame) -> dict:
    counts = scored["risk_level"].value_counts()
    return {level: int(counts.get(level, 0)) for level in ("Low", "Medium", "High")}
