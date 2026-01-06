"""
检查FastAPI服务状态
"""
import requests
import socket
import sys
import io
from pathlib import Path

# 设置UTF-8编码（Windows）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_port(host, port):
    """检查端口是否被占用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def check_service(url):
    """检查服务是否响应"""
    try:
        response = requests.get(url, timeout=5)
        return True, response.status_code, response.text[:200]
    except requests.exceptions.ConnectionError:
        return False, None, "连接被拒绝 - 服务可能未启动"
    except requests.exceptions.Timeout:
        return False, None, "请求超时"
    except Exception as e:
        return False, None, str(e)

def main():
    print("=" * 60)
    print("FastAPI 服务状态检查")
    print("=" * 60)
    
    host = "localhost"
    port = 8000
    
    # 检查端口
    print(f"\n1. 检查端口 {host}:{port} 是否被占用...")
    if check_port(host, port):
        print(f"   [OK] 端口 {port} 正在被使用")
    else:
        print(f"   [FAIL] 端口 {port} 未被占用 - 服务可能未启动")
        print(f"\n   请运行以下命令启动服务：")
        print(f"   python -m uvicorn app.main:app --host 0.0.0.0 --port {port}")
        print(f"   或者运行: 启动FastAPI.bat")
        return
    
    # 检查服务响应
    print(f"\n2. 检查服务响应...")
    urls = [
        f"http://{host}:{port}/",
        f"http://{host}:{port}/api/v1/dashboard",
        f"http://{host}:{port}/docs",
        f"http://{host}:{port}/health"
    ]
    
    for url in urls:
        print(f"\n   测试: {url}")
        success, status, info = check_service(url)
        if success:
            print(f"   [OK] 响应成功 (状态码: {status})")
            if len(info) > 0:
                print(f"   响应内容预览: {info[:100]}...")
        else:
            print(f"   [FAIL] 请求失败: {info}")
    
    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n检查被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n检查过程中出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

