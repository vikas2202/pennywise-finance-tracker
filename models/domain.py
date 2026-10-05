"""Validated domain objects, independent of Streamlit and database drivers."""
from dataclasses import dataclass, asdict
from datetime import date
from utils.validators import money, text, day, EXPENSE_CATEGORIES, INCOME_CATEGORIES


@dataclass(frozen=True)
class Transaction:
    type: str
    amount_cents: int
    category: str
    description: str
    date: str

    @classmethod
    def from_input(cls, kind, amount, category, description, when):
        categories = EXPENSE_CATEGORIES if kind == "Expense" else INCOME_CATEGORIES
        if kind not in ("Income", "Expense") or category not in categories:
            raise ValueError("Choose a valid transaction type and category.")
        when = day(when)
        if when > date.today().isoformat():
            raise ValueError("Transactions cannot be dated in the future.")
        return cls(kind, money(amount), category, text(description, "Description", 250), when)

    def document(self):
        return asdict(self)


@dataclass(frozen=True)
class Scenario:
    name: str
    income_cents: int
    expense_cents: int
    opening_cents: int
    reduction_percent: int
    months: int

    @classmethod
    def from_input(cls, name, income, expense, opening, reduction, months):
        if isinstance(months, bool) or not isinstance(months, int) or not 1 <= months <= 36:
            raise ValueError("Choose a horizon between 1 and 36 months.")
        if isinstance(reduction, bool) or not isinstance(reduction, int) or not 0 <= reduction <= 100:
            raise ValueError("Reduction must be a whole percentage between 0 and 100.")
        return cls(text(name, "Scenario name", 80), money(income, True), money(expense, True), money(opening, True), reduction, months)

    def document(self):
        return asdict(self)
