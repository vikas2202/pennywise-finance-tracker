from streamlit.testing.v1 import AppTest
from pathlib import Path


def test_complete_app_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "ui.db"))
    monkeypatch.setenv("JWT_SECRET", "t" * 32)
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=30).run()
    assert not app.exception
    def field(label): return next(x for x in app.text_input if x.label == label)
    field("Full name").set_value("Test Student")
    field("Email address").set_value("student@example.com")
    field("Choose a password").set_value("password123")
    field("Confirm password").set_value("password123")
    next(x for x in app.button if x.label == "Create account").click().run()
    assert not app.exception
    next(x for x in app.button if x.label == "Load sample data").click().run()
    assert not app.exception
    assert len(app.metric) == 4
    for page in ["Transactions", "Budgets", "Savings goals", "Analytics", "Reports", "Forecast Lab", "What-if Planner", "Spending review", "Savings coach", "Overview"]:
        next(x for x in app.radio if x.label == "Workspace").set_value(page).run()
        assert not app.exception, page
    next(x for x in app.radio if x.label == "Workspace").set_value("What-if Planner").run()
    next(x for x in app.slider if x.label == "Reduce monthly spending by (%)").set_value(25).run()
    next(x for x in app.button if x.label == "Save scenario snapshot").click().run()
    assert not app.exception
    assert any("Scenario saved" in x.value for x in app.success)
    next(x for x in app.radio if x.label == "Workspace").set_value("Overview").run()
    next(x for x in app.radio if x.label == "Workspace").set_value("What-if Planner").run()
    selector = next(x for x in app.selectbox if x.label == "Start with")
    assert len(selector.options) == 2
    next(x for x in app.radio if x.label == "Workspace").set_value("Savings coach").run()
    next(x for x in app.slider if x.label == "Shopping reduction (%)").set_value(20).run()
    next(x for x in app.button if x.label == "Save my savings plan").click().run()
    assert not app.exception
    action = next(x for x in app.checkbox if 'Shopping · try' in x.label)
    action.check().run()
    assert not app.exception
    assert any('1 of 1 actions completed' in str(x.value) for x in app.get('progress')) or next(x for x in app.checkbox if 'Shopping · try' in x.label).value
    next(x for x in app.button if x.label == "Sign out").click().run()
    assert "token" not in app.session_state
    assert not app.exception


def test_demo_onboarding_without_account(tmp_path, monkeypatch):
    monkeypatch.setenv('STORAGE_BACKEND','sqlite')
    monkeypatch.setenv('SQLITE_PATH',str(tmp_path/'demo_start.db'))
    monkeypatch.setenv('JWT_SECRET','d'*32)
    app=AppTest.from_file(Path(__file__).resolve().parents[1]/'app.py',default_timeout=30).run()
    next(x for x in app.button if x.label=='Explore a live demo →').click().run()
    assert not app.exception
    assert app.session_state.demo_mode
    next(x for x in app.button if x.label=='Discover where I can save →').click().run()
    assert app.session_state.workspace_page=='Savings coach'
    assert not app.exception
    next(x for x in app.button if x.label=='Exit demo').click().run()
    assert 'demo_store' not in app.session_state
    assert not app.exception
