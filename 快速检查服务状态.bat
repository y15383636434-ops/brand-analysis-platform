@echo off
chcp 65001 >nul
echo ========================================
echo 检查FastAPI服务状态
echo ========================================
echo.

echo 1. 检查端口8000是否被监听...
netstat -ano | findstr ":8000" | findstr "LISTENING"
if %errorlevel% equ 0 (
    echo [OK] 端口8000正在监听
) else (
    echo [错误] 端口8000未被监听，服务可能未运行
)
echo.

echo 2. 测试健康检查端点...
curl -s http://localhost:8000/health 2>nul
if %errorlevel% equ 0 (
    echo [OK] 服务正在运行
) else (
    echo [错误] 无法连接到服务
    echo.
    echo 请执行以下命令启动服务：
    echo   python 一键启动.py
    echo.
    echo 或者手动启动：
    echo   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
)
echo.

echo ========================================
pause








