"""Regex validation — account numbers, PAN, transaction refs, customer details."""

from __future__ import annotations

import re

ACCOUNT_RE = re.compile(r"^\d{10,16}$")          # 10–16 digits
PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")  # Indian PAN
TXN_REF_RE = re.compile(r"^TXN[A-Z0-9]{8,14}$")  # TXN + 8–14 alphanumerics
PHONE_RE = re.compile(r"^[6-9]\d{9}$")
EMAIL_RE = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
AMOUNT_RE = re.compile(r"^\d+(\.\d{1,2})?$")


def validate_account_no(value: str) -> bool:
    return bool(ACCOUNT_RE.match((value or "").strip()))


def validate_pan(value: str) -> bool:
    return bool(PAN_RE.match((value or "").strip().upper()))


def validate_txn_ref(value: str) -> bool:
    return bool(TXN_REF_RE.match((value or "").strip().upper()))


def validate_phone(value: str) -> bool:
    return bool(PHONE_RE.match((value or "").strip()))


def validate_email(value: str) -> bool:
    return bool(EMAIL_RE.match((value or "").strip()))


def validate_amount(value: str) -> bool:
    return bool(AMOUNT_RE.match((value or "").strip()))


def generate_txn_ref(seed: str = "0000") -> str:
    """Generate a valid TXN ref (demo)."""
    import hashlib

    h = hashlib.md5(seed.encode()).hexdigest()[:10].upper()
    return f"TXN{h}"


# Extract refs / accounts from unstructured text (regex demo)
TEXT_RE = re.compile(r"TXN[A-Z0-9]{8,14}|\b\d{10,16}\b|[A-Z]{5}[0-9]{4}[A-Z]")


def extract_refs(text: str) -> list[str]:
    return TEXT_RE.findall(text or "")
