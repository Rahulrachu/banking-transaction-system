"""Run with:  python -m pytest -q"""
import pytest

from src.bank import Bank, InsufficientBalance, InvalidInput, AccountNotFound
from src.loan import emi
from src.validation import validate_pan, validate_phone, validate_txn_ref, generate_txn_ref


@pytest.fixture
def bank():
    b = Bank()
    b.open_account("Asha Rao", "9876543210", "asha@example.com", "ABCDE1234F", "Jayanagar", 10_000)
    b.open_account("Ravi Kumar", "9123456780", "ravi@example.com", "PQRST6789Z", "Jayanagar", 5_000)
    return b


def test_deposit_withdraw_transfer_and_undo(bank):
    a, b = bank.accounts.numbers()
    bank.deposit(a, 2_000)
    bank.withdraw(a, 1_000)
    bank.transfer(a, b, 3_000)
    assert bank.balance(a) == 8_000 and bank.balance(b) == 8_000
    bank.undo_last()
    assert bank.balance(a) == 11_000 and bank.balance(b) == 5_000


def test_errors(bank):
    a, b = bank.accounts.numbers()
    with pytest.raises(InsufficientBalance):
        bank.withdraw(a, 9_500)          # would break the Rs 1,000 minimum balance
    with pytest.raises(InvalidInput):
        bank.deposit(a, -5)
    with pytest.raises(AccountNotFound):
        bank.deposit("9999999999", 100)
    with pytest.raises(InvalidInput):
        bank.transfer(a, a, 100)


def test_validation():
    assert validate_pan("ABCDE1234F") and not validate_pan("ABC123")
    assert validate_phone("9876543210") and not validate_phone("1234567890")
    assert validate_txn_ref(generate_txn_ref("x"))


def test_emi():
    assert emi(100_000, 12, 12) == pytest.approx(8884.88, abs=0.01)
