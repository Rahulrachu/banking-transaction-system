"""Bank engine: accounts, deposits, withdrawals, transfers, balance enquiry and undo.

Every operation validates its input and raises a clear, specific exception, so the
user interface can show a friendly message instead of crashing.
"""

from __future__ import annotations

from datetime import datetime

from src.data_structures import AccountStore, TransactionHistory, TransferQueue, UndoStack
from src.validation import (
    generate_txn_ref,
    validate_account_no,
    validate_customer,
)

MIN_BALANCE = 1_000.0          # minimum balance a savings account must keep
DAILY_WITHDRAW_LIMIT = 200_000.0
CREDIT_TYPES = ("deposit", "transfer_in")


class BankError(Exception):
    """Base class for all banking errors."""


class InvalidInput(BankError):
    pass


class AccountNotFound(BankError):
    pass


class InsufficientBalance(BankError):
    pass


class LimitExceeded(BankError):
    pass


class Bank:
    def __init__(self, branch_code: str = "2601") -> None:
        self.accounts = AccountStore()
        self.history = TransactionHistory()
        self.queue = TransferQueue()
        self.undo_stack = UndoStack()
        self._branch = branch_code
        self._counter = 0

    # ------------------------------------------------------------------ helpers
    def _account(self, account_no: str) -> dict:
        account_no = str(account_no).strip()
        if not validate_account_no(account_no):
            raise InvalidInput(f"'{account_no}' is not a valid account number (10-16 digits).")
        acc = self.accounts.get(account_no)
        if acc is None:
            raise AccountNotFound(f"No account found with number {account_no}.")
        return acc

    @staticmethod
    def _amount(amount) -> float:
        try:
            value = round(float(amount), 2)
        except (TypeError, ValueError):
            raise InvalidInput("Amount must be a number.") from None
        if value <= 0:
            raise InvalidInput("Amount must be greater than zero.")
        if value > 10_000_000:
            raise InvalidInput("Amount is above the single-transaction cap of Rs 1,00,00,000.")
        return value

    def _record(self, acc: dict, ttype: str, amount: float, counterparty: str,
                channel: str, when: datetime | None) -> dict:
        self._counter += 1
        when = when or datetime.now()
        txn = {
            "txn_ref": generate_txn_ref(f"{acc['account_no']}{ttype}{amount}{when.isoformat()}{self._counter}"),
            "account_no": acc["account_no"],
            "customer": acc["name"],
            "type": ttype,
            "counterparty": counterparty,
            "amount": amount,
            "timestamp": when.isoformat(timespec="seconds"),
            "channel": channel,
            "balance_after": acc["balance"],
        }
        self.history.append(txn)
        return txn

    def _withdrawn_today(self, account_no: str, day) -> float:
        return sum(
            t["amount"] for t in self.history.for_account(account_no)
            if t["type"] in ("withdrawal", "transfer_out") and t["timestamp"][:10] == day.isoformat()
        )

    # ------------------------------------------------------------------ accounts
    def open_account(self, name: str, phone: str, email: str, pan: str,
                     branch: str, opening_deposit: float = MIN_BALANCE,
                     account_no: str | None = None) -> dict:
        errors = validate_customer(name, phone, email, pan)
        if errors:
            raise InvalidInput(" ".join(errors))
        if any(a["pan"] == pan.upper() for a in self.accounts.all()):
            raise InvalidInput("A customer with this PAN already has an account.")
        opening = self._amount(opening_deposit)
        if opening < MIN_BALANCE:
            raise InvalidInput(f"Opening deposit must be at least Rs {MIN_BALANCE:,.0f}.")
        if account_no is None:
            account_no = f"{self._branch}{len(self.accounts) + 1:06d}"
            while self.accounts.exists(account_no):
                account_no = str(int(account_no) + 1)
        acc = {
            "account_no": account_no,
            "name": name.strip().title(),
            "phone": phone.strip(),
            "email": email.strip().lower(),
            "pan": pan.strip().upper(),
            "branch": branch.strip() or "Main",
            "opened": datetime.now().date().isoformat(),
            "opening_balance": opening,
            "balance": opening,
        }
        self.accounts.add(acc)
        return acc

    def balance(self, account_no: str) -> float:
        return self._account(account_no)["balance"]

    # ------------------------------------------------------------- transactions
    def deposit(self, account_no: str, amount, counterparty: str = "Cash deposit",
                channel: str = "Branch", when: datetime | None = None, undoable: bool = True) -> dict:
        acc = self._account(account_no)
        value = self._amount(amount)
        acc["balance"] = round(acc["balance"] + value, 2)
        txn = self._record(acc, "deposit", value, counterparty, channel, when)
        if undoable:
            self.undo_stack.push({"kind": "single", "refs": [txn["txn_ref"]]})
        return txn

    def withdraw(self, account_no: str, amount, counterparty: str = "Cash withdrawal",
                 channel: str = "ATM", when: datetime | None = None, undoable: bool = True,
                 _type: str = "withdrawal") -> dict:
        acc = self._account(account_no)
        value = self._amount(amount)
        available = acc["balance"] - MIN_BALANCE
        if value > available:
            raise InsufficientBalance(
                f"Insufficient balance. Available to withdraw Rs {max(available, 0):,.2f} "
                f"(balance Rs {acc['balance']:,.2f}, minimum balance Rs {MIN_BALANCE:,.0f})."
            )
        day = (when or datetime.now()).date()
        if self._withdrawn_today(account_no, day) + value > DAILY_WITHDRAW_LIMIT:
            raise LimitExceeded(f"Daily debit limit of Rs {DAILY_WITHDRAW_LIMIT:,.0f} would be exceeded.")
        acc["balance"] = round(acc["balance"] - value, 2)
        txn = self._record(acc, _type, value, counterparty, channel, when)
        if undoable:
            self.undo_stack.push({"kind": "single", "refs": [txn["txn_ref"]]})
        return txn

    def transfer(self, from_no: str, to_no: str, amount, note: str = "",
                 channel: str = "NetBanking", when: datetime | None = None, undoable: bool = True) -> tuple[dict, dict]:
        if str(from_no).strip() == str(to_no).strip():
            raise InvalidInput("Cannot transfer to the same account.")
        src = self._account(from_no)
        dst = self._account(to_no)
        out = self.withdraw(src["account_no"], amount, f"To {dst['name']} ({dst['account_no'][-4:]}) {note}".strip(),
                            channel, when, undoable=False, _type="transfer_out")
        dst["balance"] = round(dst["balance"] + out["amount"], 2)
        inc = self._record(dst, "transfer_in", out["amount"],
                           f"From {src['name']} ({src['account_no'][-4:]}) {note}".strip(), channel, when)
        if undoable:
            self.undo_stack.push({"kind": "transfer", "refs": [out["txn_ref"], inc["txn_ref"]]})
        return out, inc

    # ------------------------------------------------------------- queue + undo
    def schedule_transfer(self, from_no: str, to_no: str, amount, note: str = "") -> dict:
        self._account(from_no), self._account(to_no), self._amount(amount)
        item = {"from": from_no, "to": to_no, "amount": float(amount), "note": note}
        self.queue.enqueue(item)
        return item

    def process_queue(self) -> list[tuple[dict, str]]:
        """Run all queued transfers in FIFO order. Returns (item, outcome) pairs."""
        results = []
        while len(self.queue):
            item = self.queue.dequeue()
            try:
                out, _ = self.transfer(item["from"], item["to"], item["amount"], item["note"])
                results.append((item, f"Done · {out['txn_ref']}"))
            except BankError as exc:
                results.append((item, f"Failed · {exc}"))
        return results

    def undo_last(self) -> str:
        op = self.undo_stack.pop()
        if op is None:
            raise BankError("Nothing to undo.")
        all_txns = {t["txn_ref"]: t for t in self.history.all()}
        for ref in op["refs"]:
            txn = all_txns[ref]
            acc = self.accounts.get(txn["account_no"])
            sign = 1 if txn["type"] in CREDIT_TYPES else -1
            acc["balance"] = round(acc["balance"] - sign * txn["amount"], 2)
            self.history.remove(ref)
        first = all_txns[op["refs"][0]]
        return f"Reversed {first['type'].replace('_', ' ')} of Rs {first['amount']:,.2f} ({first['txn_ref']})."
