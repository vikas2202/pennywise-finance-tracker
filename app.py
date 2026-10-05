from datetime import date
import os
import secrets

from dotenv import load_dotenv
import streamlit as st
from pymongo.errors import PyMongoError

from config.database import Store
from config.demo import DemoRepository
from ui.savings_page import SavingsPage
from ui.journey import welcome_journey
from services.auth import Auth
from services.finance import Finance
from services.analytics import frame
from ui.theme import apply_theme, hero
from ui.pages import PageContext, FunctionPage, ForecastPage, PlannerPage, ReviewPage
from ui.screens import auth_screen, dashboard, transactions, budgets, goals, analytics, reports, seed, attempt

load_dotenv()
try:
    for setting in ("STORAGE_BACKEND", "MONGO_URI", "MONGO_DB", "JWT_SECRET"):
        if setting in st.secrets and setting not in os.environ:
            os.environ[setting] = str(st.secrets[setting])
except FileNotFoundError:
    pass
st.set_page_config(page_title="Pennywise • Personal finance", page_icon="◈", layout="wide")
apply_theme()


@st.cache_resource
def resources():
    backend = os.getenv("STORAGE_BACKEND", "sqlite")
    secret = os.getenv("JWT_SECRET", "")
    if not secret and backend == "sqlite":
        secret = secrets.token_hex(32)
    return Store(backend, os.getenv("SQLITE_PATH", "data/finance.db")), secret


class FinanceApplication:
    """Composition root: maps navigation to interchangeable page objects."""
    def __init__(self):
        self.pages = {
            "Overview": FunctionPage(lambda c: dashboard(c.finance, c.data, c.period)),
            "Savings coach": SavingsPage(),
            "Transactions": FunctionPage(lambda c: transactions(c.finance, c.data)),
            "Budgets": FunctionPage(lambda c: budgets(c.finance, c.data, c.period)),
            "Savings goals": FunctionPage(lambda c: goals(c.finance)),
            "Analytics": FunctionPage(lambda c: analytics(c.data, c.finance, c.period)),
            "Forecast Lab": ForecastPage(),
            "What-if Planner": PlannerPage(),
            "Spending review": ReviewPage(),
            "Reports": FunctionPage(lambda c: reports(c.data, c.period)),
        }
        self.descriptions = {
            "Overview": "Your money at a glance. A little clarity for the decisions ahead.",
            "Savings coach": "Find the possibilities in your spending. Turn small changes into a plan.",
            "Transactions": "Every little detail, beautifully organized.",
            "Budgets": "Give your spending a plan. Make room for what matters.",
            "Savings goals": "Big dreams start with small, visible steps.",
            "Analytics": "Turn everyday transactions into a clearer picture.",
            "Forecast Lab": "Explore tomorrow with transparent models and measurable errors.",
            "What-if Planner": "Change an assumption. Discover a different possibility.",
            "Spending review": "Notice unusual expenses and understand your daily rhythm.",
            "Reports": "Your financial story, ready to take with you.",
        }

    def run(self):
        demo = st.session_state.get('demo_mode', False)
        if demo:
            if 'demo_store' not in st.session_state:
                st.session_state.demo_store = DemoRepository()
                seed(Finance(st.session_state.demo_store, 'demo'))
            store = st.session_state.demo_store
            user = {'_id':'demo', 'name':'Explorer', 'email':'Fictional demo workspace'}
        else:
            try:
                store, secret = resources()
                auth = Auth(store, secret)
            except (ValueError, KeyError, PyMongoError):
                st.error("Unable to start. Check STORAGE_BACKEND, MONGO_URI, and JWT_SECRET in your configuration. MongoDB mode requires a reachable database and a secret of at least 32 characters.")
                st.stop()
            if "token" not in st.session_state:
                auth_screen(auth)
                return
            try:
                user = auth.verify(st.session_state.token)
            except ValueError as exc:
                st.session_state.pop("token", None)
                st.error(str(exc))
                if st.button("Return to sign in"): st.rerun()
                return
        fin = Finance(store, user["_id"])
        with st.sidebar:
            st.title("◈ Pennywise")
            st.caption("YOUR PERSONAL FINANCE STUDIO")
            page = st.radio("Workspace", list(self.pages), label_visibility="collapsed", key="workspace_page")
            st.divider()
            selected_month = st.date_input("Reporting month", value=date.today().replace(day=1))
            period = selected_month.strftime("%Y-%m")
            st.caption(f"Selected month: {period}")
            st.write(user["name"])
            st.caption(user["email"])
            if st.button("Exit demo" if demo else "Sign out", width="stretch"):
                st.session_state.clear()
                st.rerun()
            st.caption("Private session · fictional data" if demo else ("Local storage · SQLite" if store.backend == "sqlite" else "Connected · MongoDB"))
            if store.backend == "sqlite": st.caption("Records persist locally. Sessions reset when the server restarts unless JWT_SECRET is configured.")
        if demo:
            st.info("You’re exploring fictional data. Changes stay in this demo session; exit to create your own account.")
        hero(page, self.descriptions[page], f"PENNYWISE STUDIO / {date.fromisoformat(period + '-01'):%B %Y}")
        if "flash" in st.session_state: st.success(st.session_state.pop("flash"))
        try:
            df = frame(fin.records("transactions"))
            if page == "Overview":
                welcome_journey(fin, df)
            if df.empty and page == "Overview":
                st.info("Start with your own transaction, or load fictional sample data to explore the dashboard.")
                if st.button("Load sample data"): attempt(lambda: seed(fin))
            self.pages[page].render(PageContext(fin, df, period))
        except PyMongoError:
            st.error("Database unavailable. Your request could not be completed. Check connectivity and try again.")


if __name__ == "__main__":
    FinanceApplication().run()
