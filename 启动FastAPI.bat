@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d %~dp0
REM 注意：不使用 --reload 参数，避免热重载导致爬虫进程被终止
REM MediaCrawler 在运行时会修改配置文件，触发热重载导致进程被杀死
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

