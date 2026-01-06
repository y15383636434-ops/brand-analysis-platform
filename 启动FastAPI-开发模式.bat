@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d %~dp0
REM ⚠️ 警告：开发模式使用 --reload 热重载
REM MediaCrawler 在运行时会修改配置文件，可能触发热重载导致爬虫进程被终止
REM 建议：仅在开发调试时使用，生产环境或运行爬虫时请使用 启动FastAPI.bat
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-exclude MediaCrawler --reload-exclude crawl_scripts --reload-exclude python_env --reload-exclude venv --reload-exclude .git --reload-exclude __pycache__ --reload-exclude data


