@echo off
REM Clarence 2.0 Launcher

echo.
echo ========================================
echo    CLARENCE 2.0 - UNIVERSAL SCRAPER
echo ========================================
echo.

REM Install dependencies
echo [*] Installing dependencies...
pip install -q -r requirements.txt

REM Clear Python cache
echo [*] Clearing cache...
if exist __pycache__ rmdir /s /q __pycache__
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

REM Run Streamlit
echo [*] Starting Streamlit...
echo [*] Open browser to http://localhost:8501
echo.

streamlit run app.py --logger.level=error

pause