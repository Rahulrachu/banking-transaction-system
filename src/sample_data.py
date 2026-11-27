"""Seeded demo data: customers and 18 months of realistic transactions.

Transactions are replayed through the real Bank engine, so every balance is
consistent and invalid debits are rejected exactly as they would be live.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from src.bank import Bank, BankError

CUSTOMERS = [
    # name, phone, email, PAN, branch, opening balance, monthly salary
    ("Rahul S R", "9019709994", "rahul.sr@example.com", "BQRPR4521K", "Jayanagar", 45_000, 62_000),
    ("P Kavi Arasu", "9886012345", "kavi.arasu@example.com", "AKPPA7732L", "Jayanagar", 38_000, 55_000),
    ("Prachodna B", "9620011223", "prachodna.b@example.com", "CHNPB1189Q", "Koramangala", 90_000, 84_000),
    ("Sarvesh M T", "9742011223", "sarvesh.mt@example.com", "DMTPS6610R", "Malleshwaram", 25_000, 41_000),
    ("Asha Rao", "9986012345", "asha.rao@example.com", "ERAPA2093M", "HSR Layout", 160_000, 1_25_000),
    ("Vikram Patil", "9885012345", "vikram.patil@example.com", "FVKPP8841N", "Whitefield", 52_000, 70_000),
]

SPEND = [
    # counterparty, channel, min, max, times per month (mean)
    ("Rent", "NetBanking", 12_000, 22_000, 1),
    ("Groceries", "UPI", 400, 4_500, 6),
    ("Electricity bill", "UPI", 900, 3_200, 1),
    ("Mobile and internet", "UPI", 400, 1_200, 1),
    ("Dining", "Card", 300, 2_800, 4),
    ("Online shopping", "Card", 600, 9_000, 2),
    ("Fuel", "Card", 500, 3_000, 3),
    ("ATM cash", "ATM", 1_000, 10_000, 2),
    ("Insurance premium", "NetBanking", 2_500, 9_000, 0.3),
]


def _when(rng: random.Random, day: datetime) -> datetime:
    # Mostly daytime; about 3% of activity happens between midnight and 4 am.
    hour = rng.randint(0, 3) if rng.random() < 0.015 else rng.randint(8, 22)
    return day.replace(hour=hour, minute=rng.randint(0, 59), second=rng.randint(0, 59))


def build_demo_bank(seed: int = 7, months: int = 18) -> Bank:
    rng = random.Random(seed)
    bank = Bank()
    now = datetime.now().replace(microsecond=0)
    start = (now - timedelta(days=30 * months)).replace(day=1, hour=9, minute=0, second=0)

    accounts = []
    for i, (name, phone, email, pan, branch, opening, salary) in enumerate(CUSTOMERS, start=1):
        acc = bank.open_account(name, phone, email, pan, branch, opening, account_no=f"2601{i:06d}")
        acc["opened"] = start.date().isoformat()
        accounts.append((acc, salary))

    events = []
    day = start
    while day <= now:
        for acc, salary in accounts:
            if day.day == 1:
                events.append((day.replace(hour=10), "salary", acc, salary * rng.uniform(0.98, 1.03)))
            for name, channel, lo, hi, per_month in SPEND:
                if rng.random() < per_month / 30:
                    scale = (salary / 70_000) ** 0.6
                    events.append((_when(rng, day), name, acc, rng.uniform(lo, hi) * scale))
            if rng.random() < 0.004:   # occasional large or unusual movement
                events.append((_when(rng, day), "Large transfer", acc, rng.uniform(50_000, 1_20_000)))
            if rng.random() < 0.02:
                events.append((_when(rng, day), "Peer transfer", acc, rng.uniform(500, 8_000)))
            if rng.random() < 0.01:
                events.append((_when(rng, day), "FD interest", acc, rng.uniform(800, 4_000)))
        day += timedelta(days=1)

    # A deliberate burst so the burst rule has something to catch.
    burst_acc = accounts[3][0]
    burst_day = (now - timedelta(days=6)).replace(hour=23)
    for k in range(4):
        events.append((burst_day + timedelta(minutes=9 * k), "Online shopping", burst_acc, rng.uniform(4_000, 9_000)))

    events.sort(key=lambda e: e[0])
    others = [a for a, _ in accounts]
    for when, kind, acc, amount in events:
        if when > now:
            continue
        amount = round(amount, 2)
        try:
            if kind == "salary":
                bank.deposit(acc["account_no"], amount, "Salary credit", "NEFT", when, undoable=False)
            elif kind == "FD interest":
                bank.deposit(acc["account_no"], amount, "FD interest", "Branch", when, undoable=False)
            elif kind in ("Large transfer", "Peer transfer"):
                to = rng.choice([o for o in others if o is not acc])
                bank.transfer(acc["account_no"], to["account_no"], amount, channel="NetBanking", when=when, undoable=False)
            else:
                channel = next(c for n, c, *_ in SPEND if n == kind)
                bank.withdraw(acc["account_no"], amount, kind, channel, when, undoable=False)
        except BankError:
            continue  # rejected just like a real bank would (e.g. insufficient balance)
    return bank
