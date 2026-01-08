import sys
from pathlib import Path
import os
import subprocess

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent

# 将根目录加入 sys.path
sys.path.insert(0, str(BASE_DIR))

# 切换工作目录到根目录
os.chdir(BASE_DIR)

def main():
    print("="*50)
    print(" 品牌分析系统启动入口")
    print("="*50)
    print(f"工作目录: {os.getcwd()}")
    
    # 转交控制权给 scripts/run.py
    script_path = BASE_DIR / "scripts" / "run.py"
    
    if not script_path.exists():
        print(f"错误: 找不到启动脚本 {script_path}")
        return
        
    # 直接运行 scripts/run.py
    try:
        subprocess.run([sys.executable, str(script_path)])
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"启动失败: {e}")

if __name__ == "__main__":
    main()
