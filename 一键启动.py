"""
一键启动服务脚本
自动启动FastAPI和Celery Worker
"""
import subprocess
import sys
import time
import os
import requests
from pathlib import Path

# 设置UTF-8编码（Windows）
if sys.platform == 'win32':
    import io
    try:
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'

# 颜色输出（Windows CMD支持）
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")

def print_header(msg):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def check_python():
    """检查Python是否可用"""
    try:
        version = sys.version_info
        print_success(f"Python版本: {version.major}.{version.minor}.{version.micro}")
        return True
    except Exception as e:
        print_error(f"Python检查失败: {e}")
        return False

def check_dependencies():
    """检查必要的依赖"""
    required_modules = ['fastapi', 'uvicorn', 'celery', 'sqlalchemy']
    missing = []
    
    for module in required_modules:
        try:
            __import__(module)
            print_success(f"模块 {module} 已安装")
        except ImportError:
            print_error(f"模块 {module} 未安装")
            missing.append(module)
    
    if missing:
        print_warning(f"缺少依赖: {', '.join(missing)}")
        print_info("请运行: pip install -r requirements.txt")
        return False
    return True

def check_port(port):
    """检查端口是否被占用"""
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            encoding='gbk',
            errors='ignore'
        )
        return f":{port}" in result.stdout
    except:
        return False

def free_port_8000():
    """释放端口8000"""
    if Path("free_port_8000.py").exists():
        try:
            subprocess.run([sys.executable, "free_port_8000.py"], 
                         capture_output=True, check=False)
            print_success("已尝试释放端口8000")
        except:
            pass

def check_redis():
    """检查Redis服务（可选）"""
    if check_port(6379):
        print_success("Redis服务运行中")
        return True
    else:
        print_warning("Redis服务未运行（可选，Celery可能需要）")
        return False

def start_celery_worker():
    """启动Celery Worker"""
    try:
        print_info("正在启动Celery Worker...")
        # 创建启动脚本内容
        startup_script = f'''@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d {os.getcwd()}
python -m celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
'''
        
        # 写入临时批处理文件
        temp_bat = Path(os.getcwd()) / "temp_start_celery.bat"
        with open(temp_bat, 'w', encoding='utf-8') as f:
            f.write(startup_script)
        
        # 使用 start 命令打开新窗口
        subprocess.Popen(
            ["start", "cmd", "/k", str(temp_bat)],
            shell=True
        )
        time.sleep(2)
        print_success("Celery Worker窗口已打开")
        return True
    except Exception as e:
        print_error(f"启动Celery Worker失败: {e}")
        return False

def start_fastapi():
    """启动FastAPI应用"""
    try:
        print_info("正在启动FastAPI应用...")
        # 创建启动脚本内容（不使用pause，直接运行）
        # 注意：去掉 --reload 参数，避免热重载导致爬虫进程被终止
        # MediaCrawler 在运行时会修改配置文件，触发热重载导致进程被杀死
        startup_script = f'''@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d {os.getcwd()}
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
'''
        
        # 写入临时批处理文件
        temp_bat = Path(os.getcwd()) / "temp_start_fastapi.bat"
        with open(temp_bat, 'w', encoding='utf-8') as f:
            f.write(startup_script)
        
        # 使用 start 命令打开新窗口，窗口会保持打开（/k 保持窗口打开）
        subprocess.Popen(
            ["start", "cmd", "/k", str(temp_bat)],
            shell=True
        )
        time.sleep(2)
        print_success("FastAPI应用窗口已打开")
        return True
    except Exception as e:
        print_error(f"启动FastAPI失败: {e}")
        return False

def check_service_health(max_retries=10, delay=2):
    """检查服务健康状态"""
    print_info("等待服务启动...")
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                print_success(f"FastAPI服务运行正常 - {data.get('status', 'unknown')}")
                return True
        except:
            if i < max_retries - 1:
                print(f"  等待中... ({i+1}/{max_retries})")
                time.sleep(delay)
            else:
                print_warning("FastAPI服务可能未完全启动，请检查FastAPI窗口")
    return False

def main():
    """主函数"""
    print_header("一键启动服务")
    
    # 切换到脚本所在目录
    os.chdir(Path(__file__).parent)
    print_info(f"工作目录: {os.getcwd()}\n")
    
    # 1. 检查Python
    print_header("步骤 1/5: 检查环境")
    if not check_python():
        input("\n按回车键退出...")
        return
    
    # 2. 检查依赖
    print("\n检查依赖...")
    if not check_dependencies():
        print_warning("部分依赖缺失，但将继续尝试启动...")
    
    # 3. 检查端口
    print("\n检查端口8000...")
    if check_port(8000):
        print_warning("端口8000已被占用")
        response = input("是否尝试释放端口? (y/n): ")
        if response.lower() == 'y':
            free_port_8000()
            time.sleep(2)
    else:
        print_success("端口8000可用")
    
    # 4. 检查Redis（可选）
    print("\n检查Redis服务...")
    check_redis()
    
    # 5. 启动服务
    print_header("步骤 2/5: 启动Celery Worker")
    celery_ok = start_celery_worker()
    
    print_header("步骤 3/5: 启动FastAPI应用")
    fastapi_ok = start_fastapi()
    
    if not celery_ok or not fastapi_ok:
        print_error("部分服务启动失败，请检查错误信息")
        input("\n按回车键退出...")
        return
    
    # 6. 等待服务启动
    print_header("步骤 4/5: 验证服务状态")
    check_service_health()
    
    # 7. 显示服务信息
    print_header("步骤 5/5: 启动完成")
    print_success("服务已启动！")
    print("\n" + "="*60)
    print("服务地址:")
    print(f"  {Colors.BOLD}API文档:{Colors.RESET} http://localhost:8000/docs")
    print(f"  {Colors.BOLD}健康检查:{Colors.RESET} http://localhost:8000/health")
    print("="*60)
    print("\n提示:")
    print("  - 已打开两个新窗口（Celery Worker 和 FastAPI）")
    print("  - 保持这两个窗口打开，关闭窗口会停止服务")
    print("  - 如需停止服务，请关闭对应的窗口")
    print("="*60 + "\n")
    
    input("按回车键退出...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消启动")
    except Exception as e:
        print_error(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")



