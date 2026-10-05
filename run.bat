@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" python -m venv .venv
if errorlevel 1 goto error
".venv\Scripts\python.exe" -c "import streamlit, pymongo, pandas, numpy, plotly, bcrypt, jwt, dotenv" >nul 2>&1
if errorlevel 1 ".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error
".venv\Scripts\python.exe" -m streamlit run app.py
goto end
:error
echo Setup failed. Check Python installation and internet access, then try again.
pause
:end
