@echo off
REM ============================================================
REM MCD AI Content Platform - Setup and Run v6 (FastAPI)
REM Framework: FastAPI + Jinja2 + HTMX
REM Default port: 8530
REM Phase 26 (2026-08-31)
REM ============================================================

setlocal enabledelayedexpansion

title MCD AI Content Platform - Setup and Run
echo.
echo ============================================================
echo   MCD AI Content Platform - Setup and Run
echo   Framework: FastAPI + Jinja2 + HTMX (Phase 26)
echo   Default port: 8530
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

REM Change to script directory (项目根)
cd /d "%~dp0"
echo [OK] Working dir: %CD%

REM Quick dep check (FastAPI + uvicorn + jinja2 + multipart)
echo [INFO] Checking FastAPI deps...
python -c "import fastapi, uvicorn, jinja2, multipart" >nul 2>&1
if errorlevel 1 (
    echo [WARN] FastAPI deps missing. Installing from web\requirements.txt...
    python -m pip install -r web\requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
    if errorlevel 1 (
        echo [ERROR] Install failed
        pause
        exit /b 1
    )
) else (
    echo [OK] FastAPI deps ready
)

REM Set port
set PORT=8530
if not "%FASTAPI_PORT%"=="" set PORT=%FASTAPI_PORT%
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

REM Start FastAPI (cd web + uvicorn)
echo.
echo ============================================================
echo   Starting on port %PORT%
echo   URL: http://localhost:%PORT%
echo ============================================================
echo.

cd /d "%~dp0web"
python -m uvicorn app:app --host 0.0.0.0 --port %PORT%

echo.
echo ============================================================
echo   FastAPI exited.
echo ============================================================
pause

endlocal