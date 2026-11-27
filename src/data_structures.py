"""Core data structures used by the bank engine.

dict         -> accounts keyed by account number (O(1) lookup)
list         -> complete, append-only transaction ledger
deque        -> rolling window of recent activity, and the FIFO transfer queue
list (stack) -> undo stack (LIFO)
defaultdict  -> transactions grouped per account
set          -> unique counterparties
"""

from __future__ import annotations

from collections import defaultdict, deque


class AccountStore:
    """Accounts stored in a dictionary: account_no -> account dict."""

    def __init__(self) -> None:
        self._accounts: dict[str, dict] = {}

    def add(self, account: dict) -> None:
        self._accounts[account["account_no"]] = account

    def get(self, account_no: str) -> dict | None:
        return self._accounts.get(account_no)

    def exists(self, account_no: str) -> bool:
        return account_no in self._accounts

    def all(self) -> list[dict]:
        return list(self._accounts.values())

    def numbers(self) -> list[str]:
        return sorted(self._accounts)

    def total_balance(self) -> float:
        return round(sum(a["balance"] for a in self._accounts.values()), 2)

    def __len__(self) -> int:
        return len(self._accounts)


class TransactionHistory:
    """Full ledger (list) plus a fixed-size window of recent entries (deque)."""

    def __init__(self, window: int = 50) -> None:
        self._log: list[dict] = []
        self._recent: deque = deque(maxlen=window)

    def append(self, txn: dict) -> None:
        self._log.append(txn)
        self._recent.append(txn)

    def remove(self, txn_ref: str) -> None:
        self._log = [t for t in self._log if t["txn_ref"] != txn_ref]
        self._recent = deque((t for t in self._recent if t["txn_ref"] != txn_ref), maxlen=self._recent.maxlen)

    def all(self) -> list[dict]:
        return list(self._log)

    def recent(self, n: int = 10) -> list[dict]:
        return list(self._recent)[-n:][::-1]

    def for_account(self, account_no: str) -> list[dict]:
        return [t for t in self._log if t["account_no"] == account_no]

    def __len__(self) -> int:
        return len(self._log)


class TransferQueue:
    """FIFO queue of scheduled transfers, processed in the order they were added."""

    def __init__(self) -> None:
        self._queue: deque = deque()

    def enqueue(self, item: dict) -> None:
        self._queue.append(item)

    def dequeue(self) -> dict | None:
        return self._queue.popleft() if self._queue else None

    def items(self) -> list[dict]:
        return list(self._queue)

    def __len__(self) -> int:
        return len(self._queue)


class UndoStack:
    """LIFO stack of reversible operations."""

    def __init__(self, limit: int = 20) -> None:
        self._stack: list[dict] = []
        self._limit = limit

    def push(self, op: dict) -> None:
        self._stack.append(op)
        if len(self._stack) > self._limit:
            self._stack.pop(0)

    def pop(self) -> dict | None:
        return self._stack.pop() if self._stack else None

    def peek(self) -> dict | None:
        return self._stack[-1] if self._stack else None

    def __len__(self) -> int:
        return len(self._stack)


def group_by_account(transactions: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for txn in transactions:
        grouped[txn["account_no"]].append(txn)
    return dict(grouped)


def unique_counterparties(transactions: list[dict]) -> set[str]:
    return {t["counterparty"] for t in transactions if t.get("counterparty")}
