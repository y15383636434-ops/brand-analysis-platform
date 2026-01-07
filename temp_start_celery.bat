@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d C:\Users\Yu\cursorProjects\githup
python -m celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
