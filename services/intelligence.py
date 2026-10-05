"""Explainable forecasting and review tools. No external AI or account data sharing."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import numpy as np
import pandas as pd
from config.repository import Repository
from models.domain import Scenario


class ForecastStrategy(ABC):
    name: str

    @abstractmethod
    def predict(self, history: list[float]) -> float:
        """Predict one month using only earlier observations."""


class LastMonth(ForecastStrategy):
    name = "Last month baseline"

    def predict(self, history):
        return float(history[-1])


class MovingAverage(ForecastStrategy):
    name = "3-month moving average"

    def predict(self, history):
        return float(np.mean(history[-3:]))


class WeightedAverage(ForecastStrategy):
    name = "Recency-weighted average"

    def predict(self, history):
        values = history[-6:]
        return float(np.average(values, weights=np.arange(1, len(values) + 1)))


@dataclass(frozen=True)
class ForecastResult:
    model: str
    estimate: float
    mae: float
    folds: int
    lower: float
    upper: float


class ForecastEngine:
    def __init__(self, strategies=None):
        self.strategies = strategies or [LastMonth(), MovingAverage(), WeightedAverage()]

    def history(self, df, today=None):
        """Exclude first observed month (may be partial) and the current month."""
        today = today or date.today()
        if df.empty:
            return pd.Series(dtype=float)
        first = pd.Period(df.date.min(), freq="M") + 1
        last = pd.Period(today, freq="M") - 1
        if first > last:
            return pd.Series(dtype=float)
        periods = pd.period_range(first, last, freq="M").astype(str)
        expenses = df[df.type == "Expense"].groupby("month").amount_cents.sum() / 100
        return expenses.reindex(periods, fill_value=0).astype(float)

    def compare(self, values):
        history = [float(x) for x in values]
        if len(history) < 4:
            raise ValueError("At least four complete months after your first recorded month are needed for a forecast and backtest.")
        if not np.all(np.isfinite(history)) or min(history) < 0:
            raise ValueError("Forecast history must contain finite nonnegative amounts.")
        results = []
        for strategy in self.strategies:
            errors = [abs(history[i] - strategy.predict(history[:i])) for i in range(3, len(history))]
            mae = float(np.mean(errors))
            estimate = max(0.0, strategy.predict(history))
            results.append(ForecastResult(strategy.name, estimate, mae, len(errors), max(0, estimate - mae), estimate + mae))
        return sorted(results, key=lambda x: x.mae)


class SpendingReviewer:
    """Each expense is compared with earlier expenses in the same category."""
    def review(self, df):
        findings = []
        expenses = df[df.type == "Expense"].sort_values(["date", "_id"])
        for _, group in expenses.groupby("category"):
            for _, row in group.iterrows():
                prior = group[group.date < row.date].amount_cents.to_numpy(dtype=float)
                if len(prior) < 5:
                    continue
                median = float(np.median(prior))
                mad = float(np.median(np.abs(prior - median)))
                threshold = max(median * 2, median + 3 * 1.4826 * mad)
                if row.amount_cents > threshold:
                    findings.append({"Date": row.date, "Description": row.description, "Category": row.category, "Amount": row.amount_cents / 100, "Earlier median": median / 100, "Review threshold": threshold / 100, "Earlier records": len(prior)})
        return pd.DataFrame(findings)


class ScenarioService:
    def __init__(self, store: Repository, user_id: str):
        self.store, self.uid = store, user_id

    @staticmethod
    def project(scenario: Scenario):
        adjusted = int((Decimal(scenario.expense_cents) * (100 - scenario.reduction_percent) / 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        months = np.arange(scenario.months + 1)
        return pd.DataFrame({"Month": months, "Current plan": (scenario.opening_cents + months * (scenario.income_cents - scenario.expense_cents)) / 100, "Adjusted plan": (scenario.opening_cents + months * (scenario.income_cents - adjusted)) / 100})

    def save(self, scenario):
        return self.store.insert("scenarios", {**scenario.document(), "user_id": self.uid, "created_at": datetime.now(timezone.utc).isoformat()})

    def saved(self):
        return self.store.find("scenarios", user_id=self.uid)

    def delete(self, record_id):
        self.store.delete("scenarios", record_id, self.uid)
