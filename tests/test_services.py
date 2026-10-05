from datetime import date, datetime, timedelta, timezone
import jwt
import mongomock
import pytest
from config.database import Store
from services.auth import Auth
from services.finance import Finance
from services.analytics import frame, totals, monthly, budget_rows, insights
from utils.validators import money


@pytest.fixture(params=["sqlite", "mongodb"])
def store(request, tmp_path):
    return Store(request.param, tmp_path / "test.db", mongomock.MongoClient().finance if request.param == "mongodb" else None)


def test_authentication(store):
    auth = Auth(store, "x" * 32)
    user = auth.register("Alice", "Alice@example.com", "password123")
    assert user["password"] != "password123"
    assert auth.verify(auth.login("alice@example.com", "password123"))["_id"] == user["_id"]
    with pytest.raises(ValueError): auth.register("Alice", "ALICE@example.com", "password123")
    with pytest.raises(ValueError): auth.login("alice@example.com", "incorrect")
    with pytest.raises(ValueError): auth.verify("broken")
    token = jwt.encode({"sub":user["_id"], "iss":"finance-tracker", "iat":datetime.now(timezone.utc)-timedelta(hours=2), "exp":datetime.now(timezone.utc)-timedelta(hours=1)}, "x"*32, algorithm="HS256")
    with pytest.raises(ValueError): auth.verify(token)
    with pytest.raises(ValueError): Auth(store, "short")


def test_transactions_and_isolation(store):
    a, b = Finance(store, "a"), Finance(store, "b")
    a.save_transaction("Income", "1000.10", "Salary", "Pay", "2026-01-01")
    a.save_transaction("Expense", "100.05", "Shopping", "Book", "2026-01-02")
    row = a.records("transactions")[1]
    assert b.records("transactions") == []
    with pytest.raises(ValueError): b.delete("transactions", row["_id"])
    with pytest.raises(ValueError): b.save_transaction("Expense", 1, "Shopping", "Attack", "2026-01-02", row["_id"])
    assert totals(frame(a.records("transactions"))) == (1000.10, 100.05, 900.05)
    a.save_transaction("Expense", "200.01", "Shopping", "Books", "2026-01-02", row["_id"])
    assert totals(frame(a.records("transactions")))[1] == 200.01
    a.delete("transactions", row["_id"])
    assert len(a.records("transactions")) == 1


@pytest.mark.parametrize("value", [0, -1, "nan", "inf", "1.001", "bad", 1000000001])
def test_invalid_money(value):
    with pytest.raises(ValueError): money(value)


def test_validation_budget_goal(store):
    fin = Finance(store, "a")
    with pytest.raises(ValueError): fin.save_transaction("Expense", 1, "Salary", "Bad", "2026-01-01")
    with pytest.raises(ValueError): fin.save_transaction("Expense", 1, "Shopping", "", "2026-01-01")
    with pytest.raises(ValueError): fin.save_transaction("Expense", 1, "Shopping", "Bad", "2026-02-30")
    with pytest.raises(ValueError): fin.save_transaction("Expense", 1, "Shopping", "Future", date.today()+timedelta(days=1))
    fin.save_transaction("Expense", 120, "Shopping", "Books", "2026-01-01")
    fin.budget("2026-01", "Shopping", 100)
    df = frame(fin.records("transactions"))
    row = budget_rows(df, fin.records("budgets"), "2026-01")[0]
    assert row["Usage %"] == 120 and row["Remaining"] == -20
    assert any("limit exceeded" in x for x in insights(df, fin.records("budgets"), "2026-01"))
    fin.budget("2026-01", "Shopping", 200)
    assert len(fin.records("budgets")) == 1
    fin.goal("Laptop", 50000, 1000, "2027-01-01")
    with pytest.raises(ValueError): fin.goal("Laptop", 50, 100, "2027-01-01")
    goal = fin.records("goals")[0]
    with pytest.raises(ValueError): Finance(store, "b").goal("Stolen", 50, 0, "2027-01-01", goal["_id"])
    with pytest.raises(ValueError): Finance(store, "b").delete("budgets", fin.records("budgets")[0]["_id"])


def test_empty_and_missing_months(store):
    assert totals(frame([])) == (0,0,0)
    assert monthly(frame([])).empty
    fin = Finance(store, "a")
    fin.save_transaction("Income", 100, "Salary", "Pay", "2026-01-01")
    fin.save_transaction("Expense", 50, "Shopping", "Book", "2026-03-01")
    trend = monthly(frame(fin.records("transactions")))
    assert trend.loc["2026-02"].sum() == 0


def test_sqlite_persistence(tmp_path):
    path = tmp_path / "persistent.db"
    Finance(Store(path=path), "a").save_transaction("Income", 1, "Salary", "Pay", "2026-01-01")
    assert len(Finance(Store(path=path), "a").records("transactions")) == 1
