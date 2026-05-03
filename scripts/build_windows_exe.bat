@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0\.."

if not exist logs mkdir logs
echo Build started %date% %time% > logs\build.log

python -m venv .venv >> logs\build.log 2>&1
call .venv\Scripts\activate.bat >> logs\build.log 2>&1

python -m pip install --upgrade pip >> logs\build.log 2>&1
pip install -r requirements.txt >> logs\build.log 2>&1

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

pyinstaller --noconfirm --clean --onefile --windowed ^
  --name ProcessSecurityAuditorAVPro ^
  --add-data "app\rules;app\rules" ^
  main.py >> logs\build.log 2>&1

if exist dist\ProcessSecurityAuditorAVPro.exe (
  echo SUCCESS: dist\ProcessSecurityAuditorAVPro.exe created. >> logs\build.log
  echo.
  echo SUCCESS
  echo Output: dist\ProcessSecurityAuditorAVPro.exe
) else (
  echo FAILED: EXE not created. Check logs\build.log
  echo FAILED: EXE not created. >> logs\build.log
)

pause
