"""Polymorphic pages: every page implements render(context)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from models.domain import Scenario
from services.intelligence import ForecastEngine, SpendingReviewer, ScenarioService
from services.analytics import monthly
from ui.theme import PALETTE, section_intro


@dataclass
class PageContext:
    finance: object
    data: pd.DataFrame
    period: str


class Page(ABC):
    @abstractmethod
    def render(self, context: PageContext): ...


class FunctionPage(Page):
    """Adapter lets proven screens participate in the same page interface."""
    def __init__(self, renderer):
        self.renderer = renderer

    def render(self, context):
        self.renderer(context)


def plot(fig):
    fig.update_layout(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", colorway=PALETTE, font_color="#574c77", margin=dict(l=10,r=10,t=25,b=10), legend_title_text="", transition_duration=450)
    st.plotly_chart(fig, width="stretch")


class ForecastPage(Page):
    def __init__(self, engine=None):
        self.engine = engine or ForecastEngine()

    def render(self, context):
        section_intro("01", "A forecast you can explain", "Compare three transparent models using earlier months to predict later ones.")
        history = self.engine.history(context.data)
        with st.expander("How this experiment works", expanded=len(history) < 4):
            st.write("The first observed month and the current month are excluded because they may be incomplete. Missing months between them count as zero recorded spending. Confirm that your records are complete before interpreting any estimate.")
            st.write("Starting with three months of training data, each model predicts the next observed month. Mean absolute error (MAE) measures the average error in rupees across these rolling tests. Lower is better. These are simple statistical baselines, with no claimed predictive accuracy beyond the displayed tests.")
        st.caption(f"{len(history)} usable months · Forecasts are independent of the sidebar reporting month.")
        if len(history) < 4:
            st.info("Keep at least four complete months after your first recorded month to enable evaluation. The existing tracker and planner work immediately.")
            return
        results = self.engine.compare(history.tolist())
        selected = st.selectbox("Forecast model", [r.model for r in results])
        result = next(r for r in results if r.model == selected)
        target = date.today().strftime("%Y-%m")
        a,b,c = st.columns(3)
        a.metric(f"Estimated expenses · {target}", f"₹{result.estimate:,.2f}")
        b.metric("Backtest mean error", f"₹{result.mae:,.2f}")
        c.metric("Tested months", result.folds)
        st.caption("Estimate targets the current month using completed months only. It is not an end-of-month extrapolation of current spending.")
        series = pd.DataFrame({"Month": history.index, "Recorded expenses": history.values})
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=series.Month, y=series["Recorded expenses"], name="Recorded expenses", mode="lines+markers", line=dict(color=PALETTE[0], width=3), fill="tozeroy", fillcolor="rgba(118,98,239,.07)"))
        fig.add_trace(go.Scatter(x=[series.Month.iloc[-1], target], y=[series["Recorded expenses"].iloc[-1], result.estimate], name="Estimate", mode="lines+markers", line=dict(color=PALETTE[1], dash="dot", width=3)))
        fig.update_yaxes(title="Amount (INR)")
        plot(fig)
        st.caption(f"Illustrative error range: ₹{result.lower:,.2f}–₹{result.upper:,.2f} (estimate ± backtest MAE). This is not a calibrated probability interval.")
        comparison = pd.DataFrame([{"Model": r.model, "Estimate (INR)": round(r.estimate,2), "MAE (INR)": round(r.mae,2), "Test months": r.folds} for r in results])
        st.subheader("Model comparison")
        st.dataframe(comparison, hide_index=True, width="stretch")
        st.download_button("Download evaluation CSV", comparison.to_csv(index=False), "forecast-evaluation.csv", "text/csv")
        if result.folds < 6:
            st.warning("This evaluation has fewer than six test months. Model rankings can change substantially as more data arrives.")


class PlannerPage(Page):
    def render(self, context):
        section_intro("02", "Small changes. Visible possibilities.", "Move the sliders to compare your current plan with a lower-spending scenario.")
        service = ScenarioService(context.finance.store, context.finance.uid)
        historical = monthly(context.data)
        saved = {r["_id"]: r for r in service.saved()}
        choice = st.selectbox("Start with", ["New scenario"] + list(saved), format_func=lambda k: saved[k]["name"] if k in saved else k)
        old = saved.get(choice, {})
        a,b = st.columns([1,1.6], gap="large")
        with a, st.container(border=True):
            name = st.text_input("Scenario name", value=old.get("name", "My next chapter"), key=f"scenario_name_{choice}")
            income = st.number_input("Expected monthly income (INR)", min_value=0., max_value=1e9, value=float(old.get("income_cents", int(historical.Income.mean()*100) if not historical.empty else 5000000))/100, step=1000., key=f"scenario_income_{choice}")
            expense = st.number_input("Expected monthly expenses (INR)", min_value=0., max_value=1e9, value=float(old.get("expense_cents", int(historical.Expense.mean()*100) if not historical.empty else 3000000))/100, step=1000., key=f"scenario_expense_{choice}")
            opening = st.number_input("Starting savings (INR)", min_value=0., max_value=1e9, value=old.get("opening_cents",0)/100, step=1000., key=f"scenario_opening_{choice}")
            reduction = st.slider("Reduce monthly spending by (%)", 0, 100, old.get("reduction_percent",10), key=f"scenario_reduction_{choice}")
            months = st.slider("Planning horizon (months)", 1, 36, old.get("months",12), key=f"scenario_months_{choice}")
        try:
            scenario = Scenario.from_input(name, income, expense, opening, reduction, months)
        except ValueError as exc:
            st.error(str(exc))
            return
        projection = service.project(scenario)
        with b:
            last = projection.iloc[-1]
            x,y = st.columns(2)
            x.metric("Projected savings", f"₹{last['Adjusted plan']:,.2f}")
            y.metric("Difference from current plan", f"₹{last['Adjusted plan'] - last['Current plan']:,.2f}")
            fig = px.line(projection, x="Month", y=["Current plan", "Adjusted plan"], color_discrete_map={"Current plan":"#b3a9ca","Adjusted plan":"#7662ef"}, markers=True, labels={"value":"Projected savings (INR)"})
            plot(fig)
            st.caption("A deterministic what-if calculation: constant monthly income and expenses, no interest, inflation, tax changes, or unexpected costs. Starting suggestions use recorded monthly averages, which may include a partial month. Edit them to match your assumptions.")
            if last["Adjusted plan"] < 0:
                st.warning("This scenario spends more than its available savings over the selected horizon.")
            if st.button("Save scenario snapshot", type="primary"):
                service.save(scenario)
                st.success("Scenario saved. Choose it from ‘Start with’ to load its assumptions.")
            st.download_button("Download projection CSV", projection.to_csv(index=False), "scenario-projection.csv", "text/csv")
        if old:
            with st.expander("Remove saved scenario"):
                confirmed = st.checkbox("Confirm scenario deletion", key=f"confirm_{choice}")
                if st.button("Delete scenario", disabled=not confirmed):
                    service.delete(choice)
                    st.rerun()


class ReviewPage(Page):
    def __init__(self, reviewer=None):
        self.reviewer = reviewer or SpendingReviewer()

    def render(self, context):
        section_intro("03", "Spot the spending that stands out", "A transparent review queue built from your own category history.")
        findings = self.reviewer.review(context.data)
        st.caption("Uses all recorded history, independent of the sidebar month. A flag is a review prompt, not evidence of fraud or an incorrect transaction.")
        with st.expander("Why a transaction is flagged"):
            st.write("A category needs at least five transactions on earlier dates. A transaction is flagged when it exceeds both twice the earlier median and the median plus three scaled median absolute deviations (MAD). Same-day and future records are excluded from its baseline. With a zero MAD, the twice-median threshold still applies.")
        if findings.empty:
            st.success("No transactions meet the review threshold.")
            st.caption("Sparse category histories cannot yet be assessed. Add more records to build a meaningful baseline.")
        else:
            st.metric("Transactions to review", len(findings))
            cats = st.multiselect("Review categories", sorted(findings.Category.unique()), default=sorted(findings.Category.unique()))
            st.dataframe(findings[findings.Category.isin(cats)], hide_index=True, width="stretch")
        st.subheader("Daily spending rhythm")
        expenses = context.data[(context.data.type == "Expense") & (context.data.month == context.period)]
        days = pd.date_range(context.period + "-01", periods=pd.Period(context.period).days_in_month)
        values = expenses.groupby("date").amount_cents.sum().reindex(days.strftime("%Y-%m-%d"), fill_value=0)/100
        observed = days.date <= date.today()
        calendar = pd.DataFrame({"Date":days[observed], "Expenses":values.to_numpy()[observed]})
        if calendar.empty:
            st.info("The selected month has not started yet.")
        else:
            plot(px.bar(calendar, x="Date", y="Expenses", color="Expenses", color_continuous_scale=["#e9e0ff", "#7662ef"], labels={"Expenses":"Expenses (INR)"}))
