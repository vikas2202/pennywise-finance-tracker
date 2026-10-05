from datetime import date
from decimal import Decimal, InvalidOperation
import re

EXPENSE_CATEGORIES = ["Food & dining", "Shopping", "Transport", "Housing", "Utilities", "Health", "Education", "Entertainment", "Travel", "Other"]
INCOME_CATEGORIES = ["Salary", "Freelance", "Investment", "Gift", "Other income"]


def money(value, allow_zero=False):
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount < 0 or (amount == 0 and not allow_zero) or amount > 1000000000:
            raise ValueError("Enter a positive amount up to 1,000,000,000.")
        if amount != amount.quantize(Decimal("0.01")):
            raise ValueError("Use at most two decimal places.")
        return int(amount * 100)
    except (InvalidOperation, TypeError) as exc:
        raise ValueError("Enter a valid amount.") from exc


def text(value, label, maximum=120):
    value = str(value).strip()
    if not value or len(value) > maximum:
        raise ValueError(f"{label} is required and must be at most {maximum} characters.")
    return value


def email(value):
    value = str(value).strip().lower()
    if len(value) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
        raise ValueError("Enter a valid email address.")
    return value


def day(value):
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError as exc:
        raise ValueError("Enter a valid date.") from exc
