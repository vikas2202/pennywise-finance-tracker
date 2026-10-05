from datetime import date, datetime, timezone
from utils.validators import money, text, day, EXPENSE_CATEGORIES, INCOME_CATEGORIES
from models.domain import Transaction
from config.repository import Repository


class Finance:
    def __init__(self, store: Repository, user_id: str):
        self.store, self.uid = store, user_id

    def records(self, kind):
        return self.store.find(kind, user_id=self.uid)

    def save_transaction(self, kind, amount, category, description, when, record_id=None):
        doc = Transaction.from_input(kind, amount, category, description, when).document()
        if record_id:
            self.store.update("transactions", record_id, self.uid, doc)
        else:
            self.create("transactions", doc)

    def create(self, kind, doc):
        return self.store.insert(kind, {**doc, "user_id": self.uid, "created_at": datetime.now(timezone.utc).isoformat()})

    def budget(self, period, category, amount):
        day(period + "-01")
        if category not in ["Overall"] + EXPENSE_CATEGORIES:
            raise ValueError("Choose a valid expense category.")
        value = money(amount)
        existing = self.store.find("budgets", user_id=self.uid, period=period, category=category)
        if existing:
            self.store.update("budgets", existing[0]["_id"], self.uid, {"limit_cents": value})
        else:
            self.create("budgets", {"period": period, "category": category, "limit_cents": value})

    def goal(self, name, target, current, deadline, record_id=None):
        target, current = money(target), money(current, allow_zero=True)
        if current > target:
            raise ValueError("Saved amount cannot exceed the target.")
        doc = {"name": text(name, "Goal name"), "target_cents": target, "current_cents": current, "deadline": day(deadline)}
        if record_id:
            self.store.update("goals", record_id, self.uid, doc)
        else:
            self.create("goals", doc)

    def delete(self, kind, record_id):
        if kind not in ("transactions", "budgets", "goals"):
            raise ValueError("Invalid record type.")
        self.store.delete(kind, record_id, self.uid)
