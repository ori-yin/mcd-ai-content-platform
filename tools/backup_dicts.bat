@echo off
REM backup_dicts.bat — 双击运行字典本地备份
REM 备份文件：data/.backups/dicts_YYYY-MM-DD_HHMMSS.tar.gz
REM 保留 14 天；详见 tools/backup_dicts.py 注释

chcp 65001 >nul
cd /d "%~dp0\.."

echo.
echo ===== 字典本地备份（保留 14 天）=====
echo.

python tools\backup_dicts.py %*

echo.
echo ===== 完成 =====
echo.
pause
