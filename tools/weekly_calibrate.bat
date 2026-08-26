@echo off
REM ============================================================
REM  weekly_calibrate.bat — 每周一上午手动跑一次 CTR 反哺校准
REM  Handoff §6.2 #3 拍板：触发条件 = 一周一次手动提交
REM  详 docs/ctr-feedback-schedule.md
REM ============================================================

setlocal

echo ============================================================
echo  Weekly CTR Baseline Calibration
echo  Date: %DATE% %TIME%
echo ============================================================

REM 切换到项目根（脚本可能在 tools/ 或被双击）
cd /d "%~dp0\.."

REM 1) 检查 feedback.db 存在
if not exist "data\feedback.db" (
    echo.
    echo [WARN] data\feedback.db 不存在，请先通过 pages/05_feedback 上传上周真实数据。
    echo        或手动跑校准看 diff：python tools\calibrate_baseline.py --dry-run
    echo.
    pause
    exit /b 1
)

REM 2) 跑校准（默认 min_reach=1000 兜底 + definition=v3.1）
python tools\calibrate_baseline.py --db data\feedback.db
set RC=%errorlevel%

echo.
if %RC% == 0 (
    echo [OK] 校准完成，详见 data\ctr_baseline_v3.x.json + .bak
) else (
    echo [FAIL] 校准失败，return code=%RC%
)

echo.
pause
exit /b %RC%