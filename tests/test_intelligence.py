from datetime import date
import numpy as np
import pytest
from config.database import Store
from models.domain import Scenario, Transaction
from services.analytics import frame
from services.intelligence import ForecastEngine, LastMonth, MovingAverage, WeightedAverage, SpendingReviewer, ScenarioService


def test_forecast_backtest_has_no_future_leakage():
    result = ForecastEngine([LastMonth()]).compare([100, 200, 300, 900, 1000])[0]
    assert result.mae == 350  # |900-300| and |1000-900|
    assert result.estimate == 1000 and result.folds == 2
    assert result.lower == 650 and result.upper == 1350


def test_model_strategy_injection():
    assert MovingAverage().predict([1000,10,20,30]) == 20
    assert WeightedAverage().predict([10,20,30]) == pytest.approx(140/6)
    result = ForecastEngine().compare([100]*8)
    assert all(r.mae == 0 and r.estimate == 100 for r in result)


@pytest.mark.parametrize("history", [[], [1,2,3], [1,2,3,float('nan')], [1,2,3,-1]])
def test_forecast_rejects_insufficient_or_invalid_history(history):
    with pytest.raises(ValueError): ForecastEngine().compare(history)


def record(when, cents, rid="1", category="Shopping"):
    return dict(_id=rid, date=when, type="Expense", category=category, description="Example", amount_cents=cents)


def test_history_excludes_partial_and_current_month_and_fills_gaps():
    df = frame([record("2026-01-19",10000), record("2026-03-02",50000),record("2026-06-01",99999)])
    history = ForecastEngine().history(df, date(2026,6,15))
    assert history.index.tolist() == ["2026-02","2026-03","2026-04","2026-05"]
    assert history.tolist() == [0,500,0,0]


def test_review_excludes_same_day_and_future_baselines():
    rows = [record(f"2026-01-0{i+1}",10000,str(i)) for i in range(5)]
    rows += [record("2026-01-06",50000,"outlier"), record("2026-01-06",999999,"same-day")]
    findings = SpendingReviewer().review(frame(rows))
    assert len(findings) == 2
    assert findings["Earlier records"].tolist() == [5,5]
    assert findings["Review threshold"].tolist() == [200,200]
    assert SpendingReviewer().review(frame(rows[:4])).empty


def test_scenario_exact_rounding_and_negative_projection(tmp_path):
    scenario = Scenario.from_input("Plan", 100, 200.01, 50, 10, 2)
    projection = ScenarioService.project(scenario)
    assert projection["Adjusted plan"].tolist() == [50,-30.01,-110.02]
    assert projection["Current plan"].iloc[-1] == -150.02
    assert ScenarioService.project(Scenario.from_input("No expenses",100,200,0,100,2))["Adjusted plan"].iloc[-1] == 200


def test_scenario_persistence_isolation_and_delete(tmp_path):
    store = Store(path=tmp_path/'scenarios.db')
    a,b = ScenarioService(store,"a"), ScenarioService(store,"b")
    saved = a.save(Scenario.from_input("Plan",100,50,0,20,12))
    assert b.saved() == []
    with pytest.raises(ValueError): b.delete(saved["_id"])
    assert a.saved()[0]["income_cents"] == 10000
    a.delete(saved["_id"])
    assert a.saved() == []


@pytest.mark.parametrize("reduction,months", [(-1,12),(101,12),(1,0),(1,37),(1.5,12),(1,1.5)])
def test_scenario_rejects_bad_assumptions(reduction,months):
    with pytest.raises(ValueError): Scenario.from_input("Plan",100,50,0,reduction,months)


def test_domain_transaction_is_immutable():
    from dataclasses import FrozenInstanceError
    transaction = Transaction.from_input("Income","100.01","Salary","Pay","2026-01-01")
    assert transaction.document()["amount_cents"] == 10001
    with pytest.raises(FrozenInstanceError): transaction.amount_cents = 1
