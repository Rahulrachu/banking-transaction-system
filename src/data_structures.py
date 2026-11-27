"""Data structures for Banking Transaction & Financial Analysis (Python Activity 3, Group 4)."""

from __future__ import annotations

from collections import deque, defaultdict
from typing import Dict, List


class AccountStore:
    """Dict-backed accounts: account_no -> account dict (O(1) lookup)."""

    def __init__(self) -> None:
        self._accounts: Dict[str, dict] = {}

    def add(self, account: dict) -> None:
        self._accounts[account["account_no"]] = account

    def get(self, account_no: str) -> dict | None:
        return self._accounts.get(account_no)

    def all_numbers(self) -> List[str]:
        return sorted(self._accounts.keys())

    def total_balance(self) -> float:
        return sum(float(a.get("balance", 0)) for a in self._accounts.values())


class TransactionHistory:
    """List + deque: full log (list) and rolling window (deque, maxlen)."""

    def __init__(self, window: int = 30) -> None:
        self._log: List[dict] = []
        self._window: deque = deque(maxlen=window)

    def append(self, txn: dict) -> None:
        self._log.append(txn)
        self._window.append(txn)

    def all(self) -> List[dict]:
        return list(self._log)

    def recent(self, n: int = 10) -> List[dict]:
        return list(self._window)[-n:]

    def total(self) -> int:
        return len(self._log)


class PendingQueue:
    """Queue (FIFO) for pending transfers to process in order."""

    def __init__(self) -> None:
        self._queue: deque = deque()

    def enqueue(self, txn: dict) -> None:
        self._queue.append(txn)

    def dequeue(self) -> dict | None:
        return self._queue.popleft() if self._queue else None

    def pending(self) -> List[dict]:
        return list(self._queue)


class UndoStack:
    """Stack (LIFO) of applied transactions for undo demo."""

    def __init__(self) -> None:
        self._stack: List[dict] = []

    def push(self, txn: dict) -> None:
        self._stack.append(txn)

    def pop(self) -> dict | None:
        return self._stack.pop() if self._stack else None

    def peek(self) -> dict | None:
        return self._stack[-1] if self._stack else None


def group_by_account(transactions: List[dict]) -> Dict[str, List[dict]]:
    """Group transactions by account using defaultdict(list)."""
    grouped: Dict[str, List[dict]] = defaultdict(list)
    for txn in transactions:
        grouped[txn.get("account_no", "Unknown")].append(txn)
    return dict(grouped)


# Set demo: unique counterparties
def unique_counterparties(transactions: List[dict]) -> List[str]:
    return sorted({t.get("counterparty", "") for t in transactions if t.get("counterparty")})
