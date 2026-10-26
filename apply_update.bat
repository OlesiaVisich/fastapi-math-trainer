@echo off
rem Скопируйте файл update.bundle в папку проекта, затем запустите этот файл двойным кликом
cd /d "%~dp0"
git bundle verify update.bundle
if errorlevel 1 (echo БАНДЛ НЕ НАЙДЕН или поврежден & pause & exit /b 1)
git fetch update.bundle website-for-teachers-d6b6d:website-for-teachers-new
git checkout -f website-for-teachers-new
git reset --hard website-for-teachers-new
if exist test.db del test.db
pip install -r requirements.txt
python init_db.py
echo.
echo Готово! Теперь запустите сервер:  py -m uvicorn app.main:app --reload
pause
