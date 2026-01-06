"""
为每个平台生成独立的MediaCrawler爬取脚本
"""
from pathlib import Path
from typing import Dict
from loguru import logger
from datetime import datetime
from app.services.login_checker import LoginChecker

# MediaCrawler平台代码映射
MEDIACRAWLER_PLATFORM_MAP = {
    "xhs": "xhs",
    "douyin": "dy",
    "weibo": "wb",
    "zhihu": "zhihu",
    "bilibili": "bili",
    "kuaishou": "ks",
    "tieba": "tieba",
}

# 平台特性配置
PLATFORM_FEATURES = {
    "xhs": {"supports_note_type": True, "supports_comments": True},
    "douyin": {"supports_note_type": False, "supports_comments": True},
    "weibo": {"supports_note_type": False, "supports_comments": True},
    "zhihu": {"supports_note_type": False, "supports_comments": True},
    "bilibili": {"supports_note_type": False, "supports_comments": True},
    "kuaishou": {"supports_note_type": False, "supports_comments": True},
    "tieba": {"supports_note_type": False, "supports_comments": True},
}


class ScriptGenerator:
    """脚本生成器"""
    
    def __init__(self, mediacrawler_path: Path, scripts_dir: Path = None):
        """
        初始化脚本生成器
        
        Args:
            mediacrawler_path: MediaCrawler根目录
            scripts_dir: 脚本保存目录，默认为项目根目录下的crawl_scripts
        """
        self.mediacrawler_path = mediacrawler_path
        if scripts_dir is None:
            # 从app/services/script_generator.py -> app/services -> app -> project_root
            project_root = Path(__file__).parent.parent.parent.parent
            scripts_dir = project_root / "crawl_scripts"
        self.scripts_dir = Path(scripts_dir).resolve()
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"脚本目录: {self.scripts_dir}")
        
        # 初始化登录检查器
        self.login_checker = LoginChecker(str(mediacrawler_path))
    
    def generate_script(
        self,
        platform: str,
        keywords: str,
        max_items: int = 10,
        note_type: str = "all",
        include_comments: bool = True,
        include_sub_comments: bool = False
    ) -> Path:
        """
        为指定平台生成爬取脚本
        
        Args:
            platform: 平台代码
            keywords: 关键词（逗号分隔）
            max_items: 最大爬取数量
            note_type: 笔记类型（仅小红书支持）
            include_comments: 是否包含评论
            include_sub_comments: 是否包含子评论
            
        Returns:
            生成的脚本文件路径
        """
        # 获取MediaCrawler平台代码
        mediacrawler_platform = MEDIACRAWLER_PLATFORM_MAP.get(platform, platform)
        
        # 获取平台特性
        features = PLATFORM_FEATURES.get(platform, {})
        
        # 如果平台不支持笔记类型，使用默认值
        if not features.get("supports_note_type", False):
            note_type = "all"
        
        # 生成脚本文件名（包含时间戳，避免冲突）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        script_filename = f"crawl_{platform}_{timestamp}.py"
        script_path = self.scripts_dir / script_filename
        
        # 确定Python解释器
        python_cmd = "python"
        python_env = self.mediacrawler_path / "python_env" / "python.exe"
        if python_env.exists():
            python_cmd = str(python_env.resolve())
        
        # main.py路径
        main_py = self.mediacrawler_path / "main.py"
        main_py_abs = str(main_py.resolve())
        
        # 检查登录状态，如果已登录则使用cookie模式，避免每次都需要扫码
        login_type = "qrcode"  # 默认使用二维码登录
        if self.login_checker.check_login_status(platform):
            login_type = "cookie"  # 已登录，使用cookie模式
            logger.info(f"[{platform}] 检测到已保存的登录状态，使用cookie模式，无需扫码")
        else:
            logger.info(f"[{platform}] 未检测到登录状态，使用二维码登录模式")
        
        # 构建命令参数
        cmd_parts = [
            python_cmd,
            main_py_abs,
            "--platform", mediacrawler_platform,
            "--lt", login_type,  # 如果已登录则使用cookie，否则使用qrcode
            "--type", "search",
            "--keywords", keywords,
            "--save_data_option", "json",
        ]
        
        # 笔记类型（仅支持笔记类型的平台）
        if features.get("supports_note_type", False):
            cmd_parts.extend(["--note_type", note_type])
        
        # 评论设置
        if include_comments:
            cmd_parts.extend(["--get_comment", "yes"])
            if include_sub_comments:
                cmd_parts.extend(["--get_sub_comment", "yes"])
            else:
                cmd_parts.extend(["--get_sub_comment", "no"])
        else:
            cmd_parts.extend(["--get_comment", "no"])
            cmd_parts.extend(["--get_sub_comment", "no"])
        
        # 生成脚本内容
        script_content = f'''"""
自动生成的MediaCrawler爬取脚本
平台: {platform} ({mediacrawler_platform})
关键词: {keywords}
最大数量: {max_items}
生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
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
mediacrawler_path = Path(r"{self.mediacrawler_path.resolve()}")

# 命令参数
cmd = {cmd_parts}

# 工作目录
work_dir = str(mediacrawler_path)

# 执行命令
print("=" * 70)
print(f"开始爬取: {platform}")
print(f"关键词: {keywords}")
print(f"最大数量: {max_items}")
print("=" * 70)
print(f"工作目录: {{work_dir}}")
print(f"执行命令: {{' '.join(cmd)}}")
print("=" * 70)

try:
    # 使用Popen实时捕获输出并转发到stdout，这样Web界面可以捕获
    # 同时设置shell=False以确保输出能被正确捕获
    import subprocess
    import os
    
    # 确保工作目录存在
    if not os.path.exists(work_dir):
        print(f"错误: 工作目录不存在: {{work_dir}}")
        sys.exit(1)
    
    # 确保 main.py 存在
    main_py_path = Path(work_dir) / "main.py"
    if not main_py_path.exists():
        print(f"错误: main.py 不存在: {{main_py_path}}")
        sys.exit(1)
    
    # 打印调试信息
    print(f"调试信息:")
    print(f"  - 工作目录: {{work_dir}}")
    print(f"  - main.py 路径: {{main_py_path}}")
    print(f"  - Python 命令: {{cmd[0]}}")
    print(f"  - MediaCrawler main.py: {{cmd[1]}}")
    print(f"  - 完整命令: {{' '.join(cmd)}}")
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
    print(f"  - Python 目录: {{python_dir}}")
    if os.path.exists(python_scripts_dir):
        print(f"  - Scripts 目录: {{python_scripts_dir}}")
    print(f"  - 当前 PATH (前200字符): {{env.get('PATH', '')[:200]}}")
    
    # 打印最终的命令和环境变量信息（用于调试）
    print(f"最终执行命令:")
    print(f"  - 命令: {{' '.join(cmd)}}")
    print(f"  - 工作目录: {{work_dir}}")
    print(f"  - Python可执行文件: {{cmd[0]}}")
    print(f"  - Python文件存在: {{os.path.exists(cmd[0])}}")
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
        print("\\n检测到中断信号，正在终止进程...", flush=True)
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
        print(f"读取输出时发生异常: {{str(e)}}", flush=True)
        # 继续等待进程结束
        pass
    
    # 等待进程结束
    returncode = process.wait()
    
    print("=" * 70)
    print(f"爬取完成，返回码: {{returncode}}")
    print("=" * 70)
    
    if returncode != 0:
        print(f"错误: 爬取失败，返回码 {{returncode}}")
        sys.exit(returncode)
    else:
        print("爬取成功！")
        sys.exit(0)
        
except Exception as e:
    print(f"执行失败: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''
        
        # 写入脚本文件
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        logger.info(f"已生成爬取脚本: {script_path}")
        return script_path
    
    def get_script_path(self, platform: str, timestamp: str = None) -> Path:
        """
        获取脚本路径（用于查找已生成的脚本）
        
        Args:
            platform: 平台代码
            timestamp: 时间戳（可选，如果不提供则查找最新的）
            
        Returns:
            脚本文件路径
        """
        if timestamp:
            script_filename = f"crawl_{platform}_{timestamp}.py"
            return self.scripts_dir / script_filename
        else:
            # 查找最新的脚本
            pattern = f"crawl_{platform}_*.py"
            scripts = sorted(self.scripts_dir.glob(pattern), key=lambda x: x.stat().st_mtime, reverse=True)
            if scripts:
                return scripts[0]
            return None

