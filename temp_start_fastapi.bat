@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d C:\Users\Yu\cursorProjects\githup
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
