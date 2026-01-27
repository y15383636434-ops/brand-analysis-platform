import subprocess
import sys
import os
import time
from pathlib import Path

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent
os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))  # 关键：将根目录加入 sys.path

def main():
    print("="*50)
    print(" 品牌分析系统启动程序")
    print("="*50)
    print(f"工作目录: {os.getcwd()}")
    
    # 设置环境变量确保 UTF-8
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"
    
    # 启动 Celery Worker (新窗口)
    if sys.platform == "win32":
        print("[1/2] 正在启动 Celery Worker (后台任务队列)...")
        # 使用 start 命令打开新窗口
        # 注意: 需要安装 celery
        subprocess.Popen(
            ["start", "cmd", "/k", "python -m celery -A app.tasks.celery_app worker --loglevel=info --pool=solo"],
            shell=True
        )
    else:
        print("非 Windows 系统，请手动启动 Celery")

    # 等待一下
    time.sleep(2)

    # 启动 FastAPI (当前窗口)
    print("[2/2] 正在启动 FastAPI 服务...")
    print(f"访问地址: http://localhost:8000")
    print(f"API文档: http://localhost:8000/docs")
    print("-" * 50)
    
    # 自动打开浏览器
    import webbrowser
    from threading import Timer
    def open_browser():
        time.sleep(1.5)  # 等待服务启动
        webbrowser.open("http://localhost:8000")
    
    Timer(1, open_browser).start()
    
    try:
        # 移除 --reload 参数以避免 MediaCrawler 修改配置导致服务重启
        # 如果需要开发调试，请手动添加 --reload
        cmd = [
            sys.executable, "-m", "uvicorn", "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ]
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n服务已停止")

if __name__ == "__main__":
    main()
