from datetime import date, timedelta
import time
import plotly.express as px
import streamlit as st
from pymongo.errors import PyMongoError
from services.analytics import frame, totals, monthly, budget_rows, insights
from utils.validators import EXPENSE_CATEGORIES, INCOME_CATEGORIES
from ui.theme import hero, PALETTE

def attempt(fn):
    try:
        fn()
        st.session_state.flash = "Changes saved successfully."
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))
    except PyMongoError:
        st.error("Database unavailable. Check the connection and try again.")


def cash(value):
    return f"₹{value:,.2f}"


def chart(fig):
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#324954", margin=dict(l=10,r=10,t=25,b=10), legend_title_text="", transition_duration=450, template="plotly_white")
    st.plotly_chart(fig, width="stretch")


def table(df):
    st.dataframe(df[["date", "description", "category", "type", "amount"]].rename(columns=str.title), hide_index=True, width="stretch", column_config={"Amount": st.column_config.NumberColumn(format="₹%.2f")})


def auth_screen(auth):
    left, right = st.columns([1.2, 1], gap="large")
    with left:
        st.markdown('<p class="eyebrow">PENNYWISE / PERSONAL FINANCE</p>', unsafe_allow_html=True)
        hero("Make your money move with purpose.", "A colorful workspace for your everyday finances and your next big idea.", "WELCOME TO PENNYWISE")
        if st.button("Explore a live demo →", type="primary", width="stretch"):
            st.session_state.demo_mode = True
            st.rerun()
        st.caption("No signup needed. Explore with fictional data in a private session.")
        st.markdown('<div class="pw-preview"><span class="pw-tag">A LITTLE CHANGE, A NEW POSSIBILITY</span><div class="pw-preview-number">₹500 <small>/ week</small></div><p>Imagine setting aside ₹26,000 over 52 weeks.</p><div class="pw-spark"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div><span>Illustration only · no investment returns assumed</span></div>', unsafe_allow_html=True)
        st.markdown("**Discover where to save.** Build a plan, explore your future, and make progress one decision at a time.")
        st.caption("Your records stay separate from other accounts. Currency: Indian rupees (INR).")
    with right:
        with st.container(border=True):
            login, signup = st.tabs(["Sign in", "Create account"])
            with login, st.form("login"):
                st.subheader("Welcome back")
                address = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Sign in →", type="primary", width="stretch"):
                    if time.time() < st.session_state.get("retry_at", 0):
                        st.error("Please wait a moment before trying again.")
                    else:
                        try:
                            st.session_state.token = auth.login(address, password)
                            st.session_state.retry_at = 0
                            st.rerun()
                        except ValueError as exc:
                            st.session_state.retry_at = time.time() + 2
                            st.error(str(exc))
            with signup, st.form("signup"):
                name = st.text_input("Full name")
                address = st.text_input("Email address")
                password = st.text_input("Choose a password", type="password", help="At least 8 characters; at most 72 UTF-8 bytes.")
                confirm = st.text_input("Confirm password", type="password")
                if st.form_submit_button("Create account", type="primary", width="stretch"):
                    try:
                        if password != confirm:
                            raise ValueError("Passwords do not match.")
                        auth.register(name, address, password)
                        st.session_state.token = auth.login(address, password)
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))


def dashboard(fin, df, period):
    selected = df[df.month == period]
    income, expense, balance = totals(selected)
    st.caption("YOUR MONTH AT A GLANCE")
    a,b,c,d = st.columns(4)
    a.metric("Income", cash(income)); b.metric("Expenses", cash(expense))
    c.metric("Net savings", cash(balance)); d.metric("All-time balance", cash(totals(df)[2]))
    st.write("")
    left,right = st.columns([1.6,1])
    with left, st.container(border=True):
        st.subheader("Income & expenses")
        trend = monthly(df)
        if trend.empty:
            st.info("Record a transaction to start your financial timeline.")
        else:
            chart(px.bar(trend.tail(6), barmode="group", color_discrete_map={"Income":"#7662ef", "Expense":"#ff9974"}, labels={"value":"Amount (INR)","index":"Month"}))
    with right, st.container(border=True):
        st.subheader("Where your money goes")
        exp = selected[selected.type == "Expense"].groupby("category", as_index=False).amount.sum()
        if exp.empty:
            st.info("No expenses recorded for this month.")
        else:
            chart(px.pie(exp, names="category", values="amount", hole=.65, color_discrete_sequence=PALETTE))
    left,right = st.columns([1.6,1])
    with left:
        st.subheader("Recent transactions")
        table(selected.head(6))
    with right:
        st.subheader("A little perspective")
        for message in insights(df, fin.records("budgets"), period):
            st.info(message, icon="↗")
    rows = budget_rows(df, fin.records("budgets"), period)
    if rows:
        st.subheader("Monthly budget snapshot")
        for row in rows:
            st.progress(min(row["Usage %"] / 100, 1.0), text=f"{row['Category']} · {cash(row['Spent'])} of {cash(row['Limit'])} · {row['Usage %']:.0f}% used")


def transactions(fin, df):
    with st.expander("＋ Add a transaction", expanded=df.empty):
        kind = st.radio("Transaction type", ["Expense", "Income"], horizontal=True)
        with st.form("new_transaction", clear_on_submit=True):
            a,b,c = st.columns(3)
            amount = a.number_input("Amount (INR)", min_value=0.01, value=100.0, step=100.0)
            category = b.selectbox("Category", EXPENSE_CATEGORIES if kind == "Expense" else INCOME_CATEGORIES)
            when = c.date_input("Date", max_value=date.today())
            description = st.text_input("Description", placeholder="What was it for?")
            if st.form_submit_button("Save transaction", type="primary"):
                attempt(lambda: fin.save_transaction(kind, amount, category, description, when))
    a,b,c = st.columns([2,1,1])
    query = a.text_input("Search descriptions", placeholder="Search your transactions…")
    kind_filter = b.selectbox("Type", ["All", "Income", "Expense"])
    cat_filter = c.selectbox("Category filter", ["All"] + sorted(df.category.unique().tolist()))
    a,b = st.columns(2)
    start = a.date_input("From", value=date.fromisoformat(df.date.min()) if not df.empty else date.today().replace(day=1))
    end = b.date_input("To", value=date.today())
    if start > end:
        st.error("Start date must be on or before end date.")
        return
    selected = df[(df.date >= start.isoformat()) & (df.date <= end.isoformat())]
    if query:
        selected = selected[selected.description.str.contains(query, case=False, regex=False)]
    if kind_filter != "All": selected = selected[selected.type == kind_filter]
    if cat_filter != "All": selected = selected[selected.category == cat_filter]
    st.caption(f"{len(selected)} transactions · Income {cash(totals(selected)[0])} · Expenses {cash(totals(selected)[1])}")
    table(selected)
    if not selected.empty:
        with st.expander("Edit or delete a transaction"):
            docs = {r["_id"]: r for r in selected.to_dict("records")}
            rid = st.selectbox("Select transaction", list(docs), format_func=lambda k: f"{docs[k]['date']} · {docs[k]['description']} · {cash(docs[k]['amount'])}")
            row = docs[rid]
            kind = st.selectbox("Edit type", ["Expense", "Income"], index=["Expense", "Income"].index(row["type"]), key=f"type_{rid}")
            cats = EXPENSE_CATEGORIES if kind == "Expense" else INCOME_CATEGORIES
            with st.form(f"edit_{rid}_{kind}"):
                amount = st.number_input("Edit amount", min_value=.01, value=float(row["amount"]))
                category = st.selectbox("Edit category", cats, index=cats.index(row["category"]) if row["category"] in cats else 0)
                description = st.text_input("Edit description", value=row["description"])
                when = st.date_input("Edit date", value=date.fromisoformat(row["date"]), max_value=date.today())
                if st.form_submit_button("Update transaction", type="primary"):
                    attempt(lambda: fin.save_transaction(kind, amount, category, description, when, rid))
            confirm = st.checkbox("Permanently delete this transaction", key=f"del_{rid}")
            if st.button("Delete transaction", disabled=not confirm): attempt(lambda: fin.delete("transactions", rid))


def budgets(fin, df, period):
    st.write("Set an overall monthly limit, category limits, or both. Overall and category budgets are evaluated separately.")
    with st.form("budget"):
        a,b = st.columns(2)
        category = a.selectbox("Budget category", ["Overall"] + EXPENSE_CATEGORIES)
        amount = b.number_input("Monthly limit (INR)", min_value=.01, value=5000.0, step=500.0)
        if st.form_submit_button("Save budget", type="primary"):
            attempt(lambda: fin.budget(period, category, amount))
    rows = budget_rows(df, fin.records("budgets"), period)
    if not rows: st.info("Create your first budget for this month.")
    for row in rows:
        with st.container(border=True):
            st.subheader(row["Category"])
            st.progress(min(row["Usage %"] / 100, 1.0))
            st.write(f"{cash(row['Spent'])} spent / {cash(row['Limit'])} limit · {row['Usage %']:.1f}% used")
            if row["Remaining"] < 0: st.error(f"Over budget by {cash(-row['Remaining'])}")
            else: st.caption(f"{cash(row['Remaining'])} remaining")
    docs = {r["_id"]: r for r in fin.records("budgets") if r["period"] == period}
    if docs:
        with st.expander("Remove a budget"):
            rid = st.selectbox("Budget to remove", list(docs), format_func=lambda k: docs[k]["category"])
            confirm = st.checkbox("Confirm budget removal")
            if st.button("Remove budget", disabled=not confirm): attempt(lambda: fin.delete("budgets", rid))


def goals(fin):
    st.caption("Goal savings are manually tracked amounts and do not change your transaction balance.")
    docs = {r["_id"]: r for r in fin.records("goals")}
    with st.expander("Create or update a goal", expanded=not docs):
        rid = st.selectbox("Goal", ["New goal"] + list(docs), format_func=lambda k: docs[k]["name"] if k in docs else k)
        row = docs.get(rid, {})
        with st.form(f"goal_{rid}"):
            name = st.text_input("Goal name", value=row.get("name", ""), placeholder="Emergency fund")
            a,b,c = st.columns(3)
            target = a.number_input("Target (INR)", min_value=.01, value=row.get("target_cents", 1000000) / 100)
            current = b.number_input("Total saved (INR)", min_value=0.0, value=row.get("current_cents", 0) / 100)
            deadline = c.date_input("Target date", value=date.fromisoformat(row["deadline"]) if row else date.today() + timedelta(days=180))
            if st.form_submit_button("Save goal", type="primary"):
                attempt(lambda: fin.goal(name, target, current, deadline, rid if row else None))
    for rid, row in docs.items():
        with st.container(border=True):
            st.subheader(row["name"])
            ratio = row["current_cents"] / row["target_cents"]
            st.progress(ratio, text=f"{ratio:.0%} complete")
            st.write(f"{cash(row['current_cents']/100)} saved of {cash(row['target_cents']/100)} · Due {row['deadline']}")
            if ratio == 1: st.success("Goal achieved!")
            elif row["deadline"] < date.today().isoformat(): st.warning("The target date has passed. Update your plan when ready.")
            else: st.caption(f"{cash((row['target_cents'] - row['current_cents']) / 100)} to go")
            confirm = st.checkbox("Confirm deletion", key=f"goal_delete_{rid}")
            if st.button("Delete goal", key=f"goal_button_{rid}", disabled=not confirm): attempt(lambda rid=rid: fin.delete("goals", rid))


def analytics(df, fin, period):
    if df.empty:
        st.info("Add transactions to explore your spending patterns.")
        return
    st.subheader("Your financial timeline")
    trend = monthly(df)
    chart(px.line(trend, markers=True, color_discrete_map={"Income":"#7662ef", "Expense":"#ff9974"}, labels={"value":"Amount (INR)","index":"Month"}))
    st.subheader(f"Expense categories · {period}")
    selected = df[(df.month == period) & (df.type == "Expense")]
    if selected.empty: st.info("No expenses for this month.")
    else:
        data = selected.groupby("category", as_index=False).amount.sum().sort_values("amount")
        chart(px.bar(data, x="amount", y="category", orientation="h", color_discrete_sequence=["#7662ef"], labels={"amount":"Amount (INR)","category":""}))
    for msg in insights(df, fin.records("budgets"), period): st.info(msg)


def safe_csv(df):
    result = df.copy()
    for col in result.columns:
        result[col] = result[col].map(lambda x: "'" + x if isinstance(x, str) and x.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else x)
    return result.to_csv(index=False).encode("utf-8-sig")


def reports(df, period):
    selected = df[df.month == period]
    income, expense, balance = totals(selected)
    st.subheader(f"Monthly statement · {period}")
    a,b,c = st.columns(3)
    a.metric("Income", cash(income)); b.metric("Expenses", cash(expense)); c.metric("Net savings", cash(balance))
    table(selected)
    summary = selected.groupby(["type", "category"], as_index=False).amount_cents.sum()
    summary["amount"] = summary.pop("amount_cents") / 100
    st.subheader("Category summary")
    st.dataframe(summary, hide_index=True, width="stretch")
    a,b,c = st.columns(3)
    fields = ["date", "type", "category", "description", "amount"]
    a.download_button("↓ Monthly transactions CSV", safe_csv(selected[fields]), f"transactions-{period}.csv", "text/csv")
    b.download_button("↓ Category summary CSV", safe_csv(summary), f"categories-{period}.csv", "text/csv")
    c.download_button("↓ All transactions CSV", safe_csv(df[fields]), "all-transactions.csv", "text/csv")
    st.caption("CSV reports open in Excel or Google Sheets. Exports contain only your account's transactions.")


def seed(fin):
    if fin.records("transactions"):
        raise ValueError("Sample data is available only when your transaction history is empty.")
    today = date.today()
    for offset in range(10):
        first = today.replace(day=1)
        for _ in range(offset): first = (first - timedelta(days=1)).replace(day=1)
        for kind, amount, category, desc, day_num in [("Income",55000,"Salary","Monthly salary",1),("Expense",14000,"Housing","Apartment rent",1),("Expense",3200+offset*400,"Food & dining","Groceries",2),("Expense",1800,"Transport","Monthly commute",3),("Expense",9200 if offset == 0 else 2400,"Shopping","Everyday essentials",4),("Expense",1200,"Entertainment","Weekend plans",5)]:
            when = first.replace(day=day_num)
            if when <= today: fin.save_transaction(kind, amount, category, desc, when)
    fin.budget(today.strftime("%Y-%m"), "Overall", 35000)
    fin.budget(today.strftime("%Y-%m"), "Food & dining", 5000)
    fin.goal("Emergency fund", 150000, 45000, today + timedelta(days=180))


