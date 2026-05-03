@echo off
cd /d "%~dp0\.."
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HH-mm-ss"') do set datetime=%%i
git add .
git commit -m "auto update %datetime%"
git push origin main
pause
