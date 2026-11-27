"""Regular-expression validation for accounts, customers and transaction references."""

from __future__ import annotations

import hashlib
import re

ACCOUNT_RE = re.compile(r"^\d{10,16}$")                 # 10-16 digit account number
IFSC_RE = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")         # e.g. JGIB0001234
PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")         # Indian PAN, e.g. ABCDE1234F
TXN_REF_RE = re.compile(r"^TXN[A-Z0-9]{10}$")           # TXN + 10 alphanumerics
PHONE_RE = re.compile(r"^(?:\+91[\s-]?)?[6-9]\d{9}$")   # Indian mobile
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'-]{1,49}$")
AMOUNT_RE = re.compile(r"^\d{1,9}(\.\d{1,2})?$")

# Pull references, account numbers and PANs out of free text (e.g. an SMS or email)
TEXT_RE = re.compile(r"TXN[A-Z0-9]{10}|\b\d{10,16}\b|\b[A-Z]{5}[0-9]{4}[A-Z]\b")


def _clean(value) -> str:
    return str(value or "").strip()


def validate_account_no(value) -> bool:
    return bool(ACCOUNT_RE.fullmatch(_clean(value)))


def validate_ifsc(value) -> bool:
    return bool(IFSC_RE.fullmatch(_clean(value).upper()))


def validate_pan(value) -> bool:
    return bool(PAN_RE.fullmatch(_clean(value).upper()))


def validate_txn_ref(value) -> bool:
    return bool(TXN_REF_RE.fullmatch(_clean(value).upper()))


def validate_phone(value) -> bool:
    return bool(PHONE_RE.fullmatch(_clean(value)))


def validate_email(value) -> bool:
    return bool(EMAIL_RE.fullmatch(_clean(value)))


def validate_name(value) -> bool:
    return bool(NAME_RE.fullmatch(_clean(value)))


def validate_amount(value) -> bool:
    return bool(AMOUNT_RE.fullmatch(_clean(value)))


def validate_customer(name, phone, email, pan) -> list[str]:
    """Return a list of readable problems; an empty list means the details are valid."""
    errors = []
    if not validate_name(name):
        errors.append("Name should contain letters only (2-50 characters).")
    if not validate_phone(phone):
        errors.append("Phone must be a 10-digit Indian mobile number starting with 6-9.")
    if not validate_email(email):
        errors.append("Email address is not valid.")
    if not validate_pan(pan):
        errors.append("PAN must look like ABCDE1234F.")
    return errors


def generate_txn_ref(seed: str) -> str:
    """Deterministic, always-valid transaction reference."""
    return "TXN" + hashlib.sha1(seed.encode()).hexdigest()[:10].upper()


def extract_refs(text: str) -> dict:
    """Find transaction refs, account numbers and PANs inside unstructured text."""
    found = TEXT_RE.findall(text or "")
    return {
        "transaction_refs": [f for f in found if f.startswith("TXN")],
        "account_numbers": [f for f in found if f.isdigit()],
        "pans": [f for f in found if PAN_RE.fullmatch(f)],
    }
