@echo off
REM ============================================================
REM MCD AI Content Platform - Setup and Run v5 (minimal)
REM Default port: 8510
REM Skip venv (system Python already has deps), use python -m streamlit
REM ============================================================

setlocal enabledelayedexpansion

title MCD AI Content Platform - Setup and Run
echo.
echo ============================================================
echo   MCD AI Content Platform - Setup and Run
echo   Default port: 8510
echo ============================================================
echo.

REM Python check
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.11+: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version') do set PYVER=%%i
echo [OK] Python !PYVER!

REM Change to script directory
cd /d "%~dp0"
echo [OK] Working dir: %CD%

REM Quick dep check (system Python already has deps from previous run)
echo [INFO] Checking streamlit...
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo [WARN] streamlit not in system Python. Installing...
    python -m pip install streamlit pandas openpyxl jieba openai plotly pydantic pyyaml -i https://mirrors.aliyun.com/pypi/simple/
    if errorlevel 1 (
        echo [ERROR] Install failed
        pause
        exit /b 1
    )
) else (
    echo [OK] streamlit ready
)

REM Set port
set PORT=8510
if not "%STREAMLIT_PORT%"=="" set PORT=%STREAMLIT_PORT%
echo [INFO] Using port %PORT%

REM Create .env if missing
if not exist ".env" (
    copy /Y .env.example .env >nul
    echo [INFO] .env created
)

REM Port check
echo [INFO] Checking port %PORT%...
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue) { exit 1 } else { exit 0 }" >nul 2>&1
if errorlevel 1 (
    echo [WARN] Port %PORT% in use. Will try anyway.
)

REM Start streamlit (use python -m to bypass PATH issues)
echo.
echo ============================================================
echo   Starting on port %PORT%
echo   URL: http://localhost:%PORT%
echo ============================================================
echo.

start "" explorer.exe "http://localhost:%PORT%"

python -m streamlit run app.py --server.port=%PORT% --server.headless=false --browser.gatherUsageStats=false

echo.
echo ============================================================
echo   Streamlit exited.
echo ============================================================
pause

endlocal
