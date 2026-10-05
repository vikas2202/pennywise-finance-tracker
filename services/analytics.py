import pandas as pd
import numpy as np


def frame(records):
    df = pd.DataFrame(records, columns=["_id", "date", "type", "category", "description", "amount_cents"])
    df["amount_cents"] = pd.to_numeric(df["amount_cents"])
    df["amount"] = df["amount_cents"] / 100
    df["month"] = df["date"].str[:7]
    return df.sort_values("date", ascending=False)


def totals(df):
    income = int(df.loc[df.type == "Income", "amount_cents"].sum())
    expense = int(df.loc[df.type == "Expense", "amount_cents"].sum())
    return income / 100, expense / 100, (income - expense) / 100


def monthly(df):
    if df.empty:
        return pd.DataFrame(columns=["Income", "Expense"])
    result = df.pivot_table(index="month", columns="type", values="amount_cents", aggfunc="sum", fill_value=0)
    periods = pd.period_range(df.month.min(), df.month.max(), freq="M").astype(str)
    return result.reindex(index=periods, columns=["Income", "Expense"], fill_value=0) / 100


def budget_rows(df, budgets, period):
    rows = []
    expenses = df[(df.type == "Expense") & (df.month == period)]
    for b in budgets:
        if b["period"] != period:
            continue
        spent = int(expenses.amount_cents.sum()) if b["category"] == "Overall" else int(expenses.loc[expenses.category == b["category"], "amount_cents"].sum())
        rows.append({"Category": b["category"], "Limit": b["limit_cents"] / 100, "Spent": spent / 100, "Remaining": (b["limit_cents"] - spent) / 100, "Usage %": spent / b["limit_cents"] * 100})
    return rows


def insights(df, budgets, period):
    selected = df[df.month == period]
    income, expense, balance = totals(selected)
    messages = []
    if selected.empty:
        return ["Add your first transaction to see insights for this month."]
    if balance < 0:
        messages.append(f"Expenses exceed income by ₹{abs(balance):,.2f} this month.")
    elif income:
        messages.append(f"You retained {balance / income:.0%} of your recorded income this month.")
    expenses = selected[selected.type == "Expense"].groupby("category").amount_cents.sum()
    if not expenses.empty:
        messages.append(f"{expenses.idxmax()} is your largest expense category at ₹{expenses.max() / 100:,.2f}.")
    previous = str(pd.Period(period, freq="M") - 1)
    old = totals(df[df.month == previous])[1]
    if old:
        change = (expense - old) / old * 100
        if np.isfinite(change):
            messages.append(f"Spending is {abs(change):.0f}% {'higher' if change >= 0 else 'lower'} than {previous}. Current-month totals may be incomplete.")
    for row in budget_rows(df, budgets, period):
        if row["Usage %"] >= 80:
            messages.append(f"{row['Category']} budget: {row['Usage %']:.0f}% used" + (" — limit exceeded." if row["Usage %"] > 100 else "."))
    return messages
