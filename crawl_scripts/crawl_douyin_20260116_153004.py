"""
自动生成的MediaCrawler爬取脚本
平台: douyin (dy)
类型: creator
关键词: N/A
目标URL: https://www.douyin.com/user/MS4wLjABAAAADWty-TQLKn4uPxaSsFHr4LAzo-pF8aFkobdMWk2AKQtF18mpM-txpXloH7-ix31Y
最大数量: 1
生成时间: 2026-01-16 15:30:04
"""
# -*- coding: utf-8 -*-
import subprocess
import sys
import os
from pathlib import Path

# 设置标准输出编码为UTF-8（Windows）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# MediaCrawler路径
mediacrawler_path = Path(r"C:\Users\Yu\cursorProjects\githup\MediaCrawler")

# 命令参数
cmd = ['C:\\Users\\Yu\\cursorProjects\\githup\\MediaCrawler\\python_env\\python.exe', 'C:\\Users\\Yu\\cursorProjects\\githup\\MediaCrawler\\main.py', '--platform', 'dy', '--lt', 'cookie', '--type', 'creator', '--save_data_option', 'json', '--keywords', 'MS4wLjABAAAADWty-TQL', '--get_comment', 'no', '--get_sub_comment', 'no']

# 工作目录
work_dir = str(mediacrawler_path)

# 执行命令
print("=" * 70)
print(f"开始爬取: douyin")
print(f"类型: creator")
print(f"目标URL: https://www.douyin.com/user/MS4wLjABAAAADWty-TQLKn4uPxaSsFHr4LAzo-pF8aFkobdMWk2AKQtF18mpM-txpXloH7-ix31Y")
print(f"最大数量: 1")
print("=" * 70)
print(f"工作目录: {work_dir}")
print(f"执行命令: {' '.join(cmd)}")
print("=" * 70)


# ==========================================
# 动态修改配置文件
# ==========================================
import re
import traceback

config_file_path = mediacrawler_path / "config" / "dy_config.py"
backup_file_path = config_file_path.with_suffix('.py.bak')

try:
    if config_file_path.exists():
        print(f"正在修改配置文件: {config_file_path}")
        with open(config_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 备份配置文件
        with open(backup_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"已备份配置文件到: {backup_file_path}")
            
        # 替换变量值
        target_urls = ['https://www.douyin.com/user/MS4wLjABAAAADWty-TQLKn4uPxaSsFHr4LAzo-pF8aFkobdMWk2AKQtF18mpM-txpXloH7-ix31Y']
        
        # 构造新的赋值语句
        new_assignment = f'DY_CREATOR_ID_LIST = {target_urls}'
        
        # 使用正则替换整个列表定义
        # 匹配 DY_CREATOR_ID_LIST = [ ... ] (包括多行)
        pattern = r'DY_CREATOR_ID_LIST\s*=\s*\[.*?\]'
        
        print(f"配置文件路径: {config_file_path}")
        print(f"尝试匹配正则: {pattern}")
        
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            print(f"找到配置项，旧内容长度: {len(match.group(0))}")
            print(f"旧内容(前100字符): {match.group(0)[:100]}...")
            
            new_content = re.sub(pattern, new_assignment, content, flags=re.DOTALL)
            
            with open(config_file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                f.flush()
                os.fsync(f.fileno())
                
            print(f"已更新配置变量 DY_CREATOR_ID_LIST")
            print(f"新内容(前100字符): {new_assignment[:100]}...")
        else:
            print(f"警告: 未在配置文件中找到变量 DY_CREATOR_ID_LIST，尝试直接追加")
            print(f"文件内容预览(前200字符): {content[:200]}")
            # 如果没找到，尝试追加
            with open(config_file_path, 'a', encoding='utf-8') as f:
                f.write(f"\n{new_assignment}\n")
except Exception as e:
    print(f"修改配置文件失败: {e}")
    traceback.print_exc()


try:
    # 使用Popen实时捕获输出并转发到stdout，这样Web界面可以捕获
    # 同时设置shell=False以确保输出能被正确捕获
    import subprocess
    import os
    
    # 确保工作目录存在
    if not os.path.exists(work_dir):
        print(f"错误: 工作目录不存在: {work_dir}")
        sys.exit(1)
    
    # 确保 main.py 存在
    main_py_path = Path(work_dir) / "main.py"
    if not main_py_path.exists():
        print(f"错误: main.py 不存在: {main_py_path}")
        sys.exit(1)
    
    # 打印调试信息
    print(f"调试信息:")
    print(f"  - 工作目录: {work_dir}")
    print(f"  - main.py 路径: {main_py_path}")
    print(f"  - Python 命令: {cmd[0]}")
    print(f"  - MediaCrawler main.py: {cmd[1]}")
    print(f"  - 完整命令: {' '.join(cmd)}")
    print("=" * 70)
    
    # 设置环境变量，确保 Python 能找到 DLL
    env = os.environ.copy()
    # 添加 Python 虚拟环境的目录到 PATH（Windows）
    python_exe = cmd[0]
    python_dir = os.path.dirname(python_exe)
    python_scripts_dir = os.path.join(python_dir, "Scripts")
    
    # 添加 Python 目录和 Scripts 目录到 PATH
    path_parts = [python_dir]
    if os.path.exists(python_scripts_dir):
        path_parts.append(python_scripts_dir)
    
    # 更新 PATH 环境变量（确保Python虚拟环境的DLL路径在最前面）
    current_path = env.get("PATH", "")
    new_path_parts = []
    for path_part in path_parts:
        if path_part not in current_path:
            new_path_parts.append(path_part)
    
    # 将新路径添加到PATH的最前面
    if new_path_parts:
        env["PATH"] = os.pathsep.join(new_path_parts) + os.pathsep + current_path
    
    print(f"环境变量 PATH 已更新:")
    print(f"  - Python 目录: {python_dir}")
    if os.path.exists(python_scripts_dir):
        print(f"  - Scripts 目录: {python_scripts_dir}")
    print(f"  - 当前 PATH (前200字符): {env.get('PATH', '')[:200]}")
    
    # 打印最终的命令和环境变量信息（用于调试）
    print(f"最终执行命令:")
    print(f"  - 命令: {' '.join(cmd)}")
    print(f"  - 工作目录: {work_dir}")
    print(f"  - Python可执行文件: {cmd[0]}")
    print(f"  - Python文件存在: {os.path.exists(cmd[0])}")
    print("=" * 70)
    
    process = subprocess.Popen(
        cmd,
        cwd=work_dir,
        stdout=subprocess.PIPE,  # 捕获输出
        stderr=subprocess.STDOUT,  # 将错误输出合并到标准输出
        text=True,
        encoding='utf-8',
        bufsize=1,  # 行缓冲
        errors='replace',
        env=env,  # 使用修改后的环境变量
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0  # Windows下不创建新窗口
    )
    
    # 实时读取并转发输出（使用更安全的方式）
    import time
    try:
        while True:
            # 检查进程是否已结束
            if process.poll() is not None:
                break
            
            # 读取一行输出
            try:
                line = process.stdout.readline()
                if not line:
                    # 如果没有输出，等待一小段时间后继续
                    time.sleep(0.1)
                    continue
            except (ValueError, OSError) as e:
                # stdout已关闭或进程已结束
                if process.poll() is not None:
                    break
                time.sleep(0.1)
                continue
            
            # 立即输出到stdout，让Web界面捕获
            print(line.rstrip(), flush=True)
    except KeyboardInterrupt:
        # 如果进程被中断，尝试优雅地终止
        print("\n检测到中断信号，正在终止进程...", flush=True)
        if process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        # 设置返回码为130（SIGINT的标准返回码）
        sys.exit(130)
    except Exception as e:
        # 其他异常，记录但不立即退出，等待进程自然结束
        print(f"读取输出时发生异常: {str(e)}", flush=True)
        # 继续等待进程结束
        pass
    
    # 等待进程结束
    returncode = process.wait()
    
    print("=" * 70)
    print(f"爬取完成，返回码: {returncode}")
    print("=" * 70)
    
    if returncode != 0:
        print(f"错误: 爬取失败，返回码 {returncode}")
    else:
        print("爬取成功！")
        
except Exception as e:
    print(f"执行失败: {e}")
    import traceback
    traceback.print_exc()
    returncode = 1


# ==========================================
# 恢复配置文件
# ==========================================
try:
    if os.path.exists(backup_file_path):
        # 读取备份文件
        with open(backup_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # 写入原文件
        with open(config_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        # 删除备份
        os.remove(backup_file_path)
        print(f"已恢复配置文件 {config_file_path}")
    else:
        print(f"未找到备份文件，无法恢复: {backup_file_path}")
except Exception as e:
    print(f"恢复配置文件失败: {e}")
    traceback.print_exc()


# 退出
sys.exit(returncode if 'returncode' in locals() else 1)
