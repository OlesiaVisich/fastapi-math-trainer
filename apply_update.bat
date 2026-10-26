@echo off
chcp 65001 >nul
cd /d "%~dp0"
git fetch update.bundle master:website-new || (echo OSHIBKA: update.bundle ne v etoy papke & pause & exit /b 1)
git checkout -f website-new
git reset --hard website-new
if exist test.db del test.db
pip install -r requirements.txt
python init_db.py
echo.
echo GOTOVO! Zapustite server:  py -m uvicorn app.main:app --reload
pause
