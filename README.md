# Pennywise — Personal Finance and Expense Tracker

A Python and Streamlit personal finance application with income and expense tracking, budgets, savings goals, a savings coach, interactive analytics, forecast evaluation, and CSV reports. MongoDB is supported for deployment; persistent SQLite storage makes local setup simple.

## Contents

- [1. Requirements](#1-requirements)
- [2. Get the source code](#2-get-the-source-code)
- [3. Run on Windows — easiest method](#3-run-on-windows--easiest-method)
- [4. Run on Windows — manual method](#4-run-on-windows--manual-method)
- [5. First-time walkthrough](#5-first-time-walkthrough)
- [6. Stop and restart](#6-stop-and-restart)
- [7. Optional local configuration](#7-optional-local-configuration)
- [8. Optional MongoDB setup](#8-optional-mongodb-setup)
- [9. Optional Docker setup](#9-optional-docker-setup)
- [10. Run on macOS or Linux](#10-run-on-macos-or-linux)
- [11. Run tests](#11-run-tests)
- [12. Troubleshooting](#12-troubleshooting)
- [13. Backups and updates](#13-backups-and-updates)
- [14. Publish source on GitHub](#14-publish-source-on-github)
- [15. Hosting the application](#15-hosting-the-application)
- [Features](#features)
- [Structure](#structure)

## 1. Requirements

1. Install **Python 3.12 or newer** from [python.org](https://www.python.org/downloads/). On Windows, enable **Add Python to PATH** during installation.
2. Have an internet connection for the first dependency installation.
3. Use a modern browser such as Edge, Chrome, or Firefox.
4. Git is optional if downloading a ZIP; it is needed for cloning and pushing source.
5. MongoDB and Docker are **optional**. Neither is needed for the default local setup.

The last recorded development environment used Python 3.14.7 on Windows. Start with the commands below; no API key or paid service is required for the local features.

## 2. Get the source code

### Option A — Download a ZIP

1. On the GitHub repository page, choose **Code → Download ZIP**, or use the supplied project ZIP.
2. Right-click the ZIP and choose **Extract All**.
3. Open the extracted folder. If another folder is inside, open it until you see `app.py`, `requirements.txt`, and `run.bat` together.
4. Do not run directly from inside the ZIP.

### Option B — Clone with Git

1. On the repository page, choose **Code → HTTPS** and copy the clone URL.
2. Open PowerShell in the folder where you want to keep the project.
3. Run `git clone` followed by the copied URL.
4. Open the newly created project folder.

Your existing local project folder is already ready to use; downloading it again is unnecessary.

## 3. Run on Windows — easiest method

1. Open the project folder in File Explorer.
2. Double-click **run.bat**.
3. On the first run, wait while it creates `.venv` and installs packages. Downloads can take several minutes.
4. Keep the terminal window open. Wait for the local URL to appear.
5. Open **[http://localhost:8501](http://localhost:8501)** in your browser.
6. Choose **Explore a live demo** or **Create account**.

`run.bat` checks that the required modules can be imported and installs `requirements.txt` when they are missing. After updating the project, explicitly reinstall requirements as described in section 13 to apply changed versions.

## 4. Run on Windows — manual method

Run each command separately and wait for it to finish. No virtual-environment activation or PowerShell execution-policy change is required.

### Step 1 — Open PowerShell in the project folder

Open the folder in File Explorer, click its address bar, type `powershell`, and press Enter. Alternatively, use `cd` with your extracted folder path. Paths containing spaces must be quoted.

### Step 2 — Verify Python

```powershell
python --version
python -m pip --version
```

If `python` is not found, try `py --version`. You may use `py` for the environment-creation command below. If neither works, install Python and reopen PowerShell.

### Step 3 — Create the virtual environment

```powershell
python -m venv .venv
```

If the project already has a working `.venv`, skip this step. A downloaded source ZIP does not include an environment.

### Step 4 — Install the dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`requirements.txt` is the normal cross-platform installation file. `requirements-lock.txt` records the original tested environment; it is available for reproducibility, but may contain platform-specific packages.

### Step 5 — Start the application

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

### Step 6 — Open the browser

Visit **[http://localhost:8501](http://localhost:8501)**. If the terminal reports a different port, open the URL printed there.

Success looks like the Pennywise welcome screen with **Sign in**, **Create account**, and **Explore a live demo**.

## 5. First-time walkthrough

### Explore without an account

1. Click **Explore a live demo**.
2. Explore the fictional transactions, budgets, goals, charts, and forecasts.
3. Open **Savings coach**, move a category reduction slider, and inspect the potential savings.
4. Save a sample plan and try its action checklist.
5. Click **Exit demo** to discard the demo session.

The demo uses session memory. It never copies fictional records into your personal account, and its changes are not intended to survive leaving or refreshing the session.

### Create your own account

1. Select **Create account**.
2. Enter your name and email, choose a password, and confirm it.
3. Use at least eight password characters (up to 72 UTF-8 bytes).
4. Submit the form to enter your empty workspace.
5. Open **Transactions → Add a transaction**. Choose Income or Expense, amount, category, date, and description; then save.
6. Open **Budgets** to set an overall or category limit for the sidebar's reporting month.
7. Open **Savings goals** to record a target, saved amount, and deadline.
8. Open **Savings coach** to consider spending changes and save action plans.
9. Use **Analytics**, **Forecast Lab**, **What-if Planner**, and **Spending review** to explore patterns.
10. Use **Reports** to download your account's CSV reports.

For a classroom presentation, **Load sample data** is also available on Overview when the account's transaction history is empty. This adds fictional records to that account. Use a separate demonstration account if you want to keep personal records separate.

**Reporting month:** controls Overview, Budgets, Reports, and month-specific analysis. Forecast Lab and recurring-payment review use their stated history windows. Forecasts need at least four usable completed months after the first recorded month; a new account may not yet qualify.

## 6. Stop and restart

1. To stop the server, select its terminal and press **Ctrl+C**.
2. To restart, double-click `run.bat`, or rerun the Step 5 command from the project folder.
3. Reopen the local URL and sign in.

Account records persist in local storage. Without a configured `JWT_SECRET`, a server restart expires old sessions; it does not delete accounts or transactions. Closing the browser alone does not stop the server.

## 7. Optional local configuration

Default SQLite mode works without `.env`. To customize settings:

1. Stop the server.
2. Copy the example once. **Do not overwrite an existing `.env`.**

```powershell
Copy-Item .env.example .env
notepad .env
```

3. Keep `STORAGE_BACKEND=sqlite` for local storage.
4. Optionally generate a stable signing secret:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

5. Copy that generated value after `JWT_SECRET=` in `.env`, save, and restart.

| Setting | Purpose | Default |
| --- | --- | --- |
| `STORAGE_BACKEND` | `sqlite` or `mongodb` | `sqlite` |
| `SQLITE_PATH` | Local database file | `data/finance.db` |
| `MONGO_URI` | MongoDB connection URI | Set in MongoDB mode |
| `MONGO_DB` | MongoDB database name | `personal_finance` |
| `JWT_SECRET` | Session signing secret, at least 32 characters | Generated per server process in SQLite mode if unset |

Keep `.env` private. `.env.example` contains placeholders and is safe to distribute.

## 8. Optional MongoDB setup

### Use an existing local MongoDB server

1. Install and start MongoDB using its [official installation guide](https://www.mongodb.com/docs/manual/installation/), or use Docker in section 9.
2. Create `.env` as described above.
3. Set these values:

```dotenv
STORAGE_BACKEND=mongodb
MONGO_URI=mongodb://localhost:27017
MONGO_DB=personal_finance
JWT_SECRET=replace-with-your-generated-secret-of-at-least-32-characters
```

4. Replace the JWT placeholder with your generated secret.
5. Restart Streamlit and check for **Connected · MongoDB** in the sidebar after signing in.

### Use MongoDB Atlas

1. Create a cluster in your MongoDB Atlas account.
2. Create a database user with access to the application database.
3. Allow the connecting machine or hosting service through the cluster's network access settings.
4. Copy the Python driver connection string and enter your database username and password. URI-encode special characters where required.
5. Set `MONGO_URI` to that URI in `.env`; set the other values as above.
6. Restart the app. The app creates its collections and indexes through the configured database account.

Switching backends does not migrate data: SQLite accounts will not automatically appear in MongoDB. The app does not silently switch to SQLite if MongoDB is unreachable.

## 9. Optional Docker setup

1. Install and start Docker Desktop.
2. Create `.env` and set a generated `JWT_SECRET` of at least 32 characters.
3. Open a terminal in the project root and run:

```powershell
docker compose up --build
```

4. Wait for MongoDB and the app to start; then visit `http://localhost:8501`.
5. Press Ctrl+C to stop foreground execution. To stop/remove the containers while retaining the database volume, run:

```powershell
docker compose down
```

The compose configuration uses MongoDB internally and binds the web app to localhost. Data persists in the `finance_mongo` volume. Do not add `-v` to the down command unless you intend to erase that volume. This configuration is for local development, not a hardened public database deployment.

## 10. Run on macOS or Linux

Open a terminal in the extracted or cloned project folder:

```bash
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
```

Open `http://localhost:8501`. Stop with Ctrl+C. Some Linux distributions require their Python venv package to be installed before creating an environment. The automated validation recorded for this project was performed on Windows; other platforms have not been verified here.

## 11. Run tests

Stop any running test process, open the project folder, and run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -c pytest.ini
.\.venv\Scripts\python.exe -m pip check
```

On macOS/Linux, replace the interpreter path with `.venv/bin/python`. Tests use temporary databases and a MongoDB test double; they do not need a live MongoDB server. Coverage includes authentication, account isolation, transactions, calculations, budgets, goals, forecasting, scenarios, savings plans, demo separation, and UI flows. See [verification results](docs/TEST_RESULTS.md) for recorded runs and remaining limits.

## 12. Troubleshooting

| Problem | What to do |
| --- | --- |
| `python` is not recognized | Reopen the terminal after installing Python with PATH enabled; try `py` on Windows. |
| `.venv\Scripts\python.exe` is missing | Ensure you are in the folder containing app.py, then create `.venv` using section 4. |
| `No module named streamlit` or another module | Run the dependency-install command with the `.venv` interpreter. Wait for completion before starting the app. |
| `app.py` not found | Your terminal is in the wrong folder. Open the extracted inner folder containing app.py. |
| Browser cannot connect | Keep the server terminal open, check it for errors, and use its printed URL. A localhost URL works only while the app is running on your machine. |
| Port 8501 is already in use | Stop your previous server, or append `--server.port 8502` and visit localhost:8502. |
| Blank/stale page after changes | Use Streamlit's Rerun button or restart the server and refresh the browser. |
| MongoDB cannot connect | Check backend, URI, database credentials, server status, Atlas network access, and signing-secret length. |
| Incorrect email/password | Use the account created in the current database backend; email is normalized. Password reset is not implemented. |
| Forecast unavailable | More complete monthly history is needed; use the fictional demo to explore the feature immediately. |
| Export contains no rows | Check the selected reporting month and whether that account has transactions. |
| First installation is slow | Allow package downloads to finish. A local non-synced folder can avoid OneDrive synchronization overhead. |

Alternative port example:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8502
```

## 13. Backups and updates

1. Stop the server before backing up SQLite.
2. Copy `data/finance.db` to a secure backup location. Also preserve your private `.env` separately.
3. For a clean Git checkout, download the latest source or run `git pull`. Review local changes before pulling; do not overwrite your own work.
4. Reinstall dependencies after an update:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

5. Restart the app and check your account records.

For MongoDB, use your database provider's backup tools. Source ZIPs and GitHub repositories intentionally exclude real account databases, secrets, caches, and virtual environments.

## 14. Publish source on GitHub

Publishing code and hosting the application are separate actions. Uploading the repository does not make a localhost app accessible online.

1. Sign in to your GitHub account and create an empty repository named, for example, `pennywise-finance-tracker`.
2. Choose private or public visibility deliberately. Do not initialize remote files if you plan to push an existing local commit.
3. Copy the repository's HTTPS URL.
4. In a standalone copy of this project, initialize Git if necessary, review `.gitignore`, and stage only the application source and docs.
5. Configure your commit name/email if Git requests it, then commit and push to the new remote.
6. Confirm that app.py, config/, models/, services/, ui/, utils/, tests/, docs/, requirements.txt, and this README appear on GitHub.
7. Confirm that `.env`, `.streamlit/secrets.toml`, `data/`, `.venv/`, and unrelated projects are absent.

The `.gitignore` protects normal local-only files. Always inspect the staged list before publishing. Authenticate through GitHub's browser/CLI flow; do not put a personal access token in a source file or remote URL.

## 15. Hosting the application

For online access, use a Streamlit-capable host and a persistent MongoDB database. Configure `STORAGE_BACKEND=mongodb`, `MONGO_URI`, `MONGO_DB`, and a generated `JWT_SECRET` through the host's secret settings. The app also reads equivalent top-level Streamlit secrets. Use `app.py` as the entrypoint; the Docker image listens on port 8501.

SQLite on an ephemeral hosting filesystem may lose data. Before public use, configure HTTPS, authenticated database access, backups, and an external rate limiter. The built-in login delay is session-local. Email verification, password recovery, MFA, and bank integration are not implemented. See your chosen host's current documentation for account-specific deployment steps.

## Latest upgrade: savings coach and Aurora interface

- Start with **Explore a live demo** on the welcome screen. It uses fictional data in session memory, never your account database. Exit demo to discard its records and register normally.
- The Overview journey links directly to transactions, budgets, and goals. Quick actions open Savings coach and What-if Planner.
- **Savings coach** offers practical category prompts, adjustable 0–50% reductions (zero by default), exact monthly estimates, illustrative annual totals, and a goal timeline.
- Save an action plan, check off habits you tried, and download the comparison. Plan completion is not counted as verified savings.
- Recurring spending review highlights consistent descriptions across at least three months. It may include essential bills and does not assert that a payment is a subscription.
- A deeper purple-to-teal theme, animated illustration, focus states, and reduced-motion support refresh every page.

Choose a completed reporting month with complete records for useful savings estimates. Existing records are preserved. See `docs/SAVINGS_COACH.md` for methodology and limitations.

## Features

- Animated pastel interface with responsive cards, chart transitions, hover states, and reduced-motion support.
- Forecast Lab: three interchangeable statistical strategies, rolling backtests, MAE comparison, and evaluation export.
- What-if Planner: interactive assumptions, exact currency projections, saved account-specific snapshots, CSV export.
- Spending review: robust category-based unusual-expense flags and daily spending charts.
- Registration, normalized unique emails, bcrypt password hashing, eight-hour signed JWT sessions, logout.
- Dashboard with monthly income, expenses, net savings, all-time balance, category distribution, trends, recent activity, and budget usage.
- Transaction creation, editing, confirmed deletion, literal text search, type/category/date filters.
- Monthly overall and category budgets, updates, removal, percentage usage and overspending alerts.
- Savings goals with targets, total saved, deadlines, progress, editing, and deletion.
- Monthly trends, category comparisons, and transparent rule-based insights.
- Monthly transactions, category summaries, and all-history CSV exports with spreadsheet formula escaping.
- MongoDB unique indexes, account-scoped record mutations, persistent SQLite alternative, automated service/UI tests.

## Structure

```text
app.py                  FinanceApplication and authenticated page registry
models/domain.py        Immutable Transaction and Scenario models
config/repository.py    Repository protocol for business services
ui/pages.py             Page abstraction and advanced screen classes
ui/screens.py           Core finance screens
ui/theme.css            Responsive color system and reduced-motion animations
services/intelligence.py Forecast strategies, backtests, review, scenarios
config/database.py      MongoDB and SQLite repository
services/auth.py        Password hashing and JWT issuance/verification
services/finance.py     Transaction, budget, and goal rules
services/analytics.py   Pandas summaries and rule-based insights
utils/validators.py     Dates, categories, text, and exact money validation
tests/                  Service and Streamlit application tests
.streamlit/config.toml  Theme and server defaults
docs/PROJECT_GUIDE.md    Architecture, data model, demonstration and viva
```

FinanceApplication composes Page objects behind one authentication gate. Legacy screens use a FunctionPage adapter; new screens implement the Page contract directly. Domain and analysis services are independent of Streamlit. See docs/ADVANCED_DESIGN.md for the class diagram, design patterns, algorithm methodology, and suggested postgraduate evaluation.

## Calculation notes

Money is stored as integer paise (INR). Balance and net savings are income minus expenses, not independently verified bank balances. Goal amounts are manually tracked and do not create transactions. Category budgets and overall budgets are separate constraints. Savings-coach figures are hypothetical reductions chosen by the user, not confirmed savings. Forecasts are statistical baselines with measured backtest errors, not guaranteed outcomes.

## Project documentation

- [Project architecture and viva guide](docs/PROJECT_GUIDE.md)
- [Object-oriented design and forecasting methodology](docs/ADVANCED_DESIGN.md)
- [Savings coach methodology](docs/SAVINGS_COACH.md)
- [Verification results and limitations](docs/TEST_RESULTS.md)

## References

- [Python downloads](https://www.python.org/downloads/)
- [Streamlit documentation](https://docs.streamlit.io/)
- [MongoDB documentation](https://www.mongodb.com/docs/)
- [Plotly Python documentation](https://plotly.com/python/)
