"""EXTRA FEATURE 2 - Loan EMI and eligibility advisor.

Uses each customer's real transaction history to estimate how much they can
borrow, and links the interest rate to the RBI repo rate scraped live.

EMI formula:  EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
    P = principal, r = monthly interest rate, n = number of months

Eligibility uses the FOIR rule banks apply: total EMIs should stay within 50%
of average monthly income.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

FOIR = 0.50
# Indicative spread over the repo rate for each loan type (for teaching purposes)
SPREADS = {"Home loan": 2.65, "Car loan": 3.40, "Education loan": 4.25, "Personal loan": 6.50}


def emi(principal: float, annual_rate_pct: float, months: int) -> float:
    if principal <= 0 or months <= 0:
        return 0.0
    r = annual_rate_pct / 12 / 100
    if r == 0:
        return round(principal / months, 2)
    factor = (1 + r) ** months
    return round(principal * r * factor / (factor - 1), 2)


def amortization(principal: float, annual_rate_pct: float, months: int) -> pd.DataFrame:
    """Month-by-month split of each EMI into interest and principal (NumPy vectorised)."""
    pay = emi(principal, annual_rate_pct, months)
    r = annual_rate_pct / 12 / 100
    k = np.arange(1, months + 1)
    if r == 0:
        balance = principal - pay * k
    else:
        balance = principal * (1 + r) ** k - pay * (((1 + r) ** k - 1) / r)
    balance = np.clip(balance, 0, None)
    opening = np.concatenate([[principal], balance[:-1]])
    interest = opening * r
    return pd.DataFrame({
        "month": k,
        "emi": pay,
        "interest": interest.round(2),
        "principal": (pay - interest).round(2),
        "balance": balance.round(2),
    })


def monthly_income(df: pd.DataFrame, account_no: str) -> float:
    """Average monthly salary credits over the last 6 months of history."""
    sal = df[(df["account_no"] == account_no) & (df["counterparty"] == "Salary credit")]
    if sal.empty:
        sal = df[(df["account_no"] == account_no) & (df["type"] == "deposit")]
    if sal.empty:
        return 0.0
    by_month = sal.groupby("month")["amount"].sum().tail(6)
    return float(np.round(by_month.mean(), 2))


def eligibility(income: float, existing_emi: float, annual_rate_pct: float, months: int) -> dict:
    capacity = max(income * FOIR - existing_emi, 0.0)
    unit = emi(100_000, annual_rate_pct, months)          # EMI per Rs 1 lakh
    max_loan = (capacity / unit) * 100_000 if unit else 0.0
    return {
        "income": round(income, 2),
        "emi_capacity": round(capacity, 2),
        "max_loan": round(max_loan, -3),
    }
