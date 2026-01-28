@echo off
echo Uruchamianie Investment Tracker & Simulator...
cd /d "%~dp0"
python -m streamlit run app.py
pause
