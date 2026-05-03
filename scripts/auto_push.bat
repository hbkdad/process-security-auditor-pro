@echo off
cd /d %~dp0\..

echo ============================
echo Auto commit + push to GitHub
echo ============================

git status
git add .

set /p msg="Commit message: "
if "%msg%"=="" set msg=auto update

git commit -m "%msg%"
git push origin main

echo Done.
pause
