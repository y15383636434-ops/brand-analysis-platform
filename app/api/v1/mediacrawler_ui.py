"""
MediaCrawler Web界面API
提供Web界面用于选择平台、爬取类型、关键词等，并查看JSON数据
"""
from fastapi import APIRouter, Request, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List, Dict
from pydantic import ValidationError
import sys
import subprocess
import re
import json
import os
import threading
import time
import shutil
from pathlib import Path
from datetime import datetime
from loguru import logger
from app.services.script_generator import ScriptGenerator
from config import settings

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

router = APIRouter()

# 进程输出存储（进程ID -> 输出数据）
process_outputs: Dict[int, Dict] = {}
# 进程对象存储（进程ID -> 进程对象）
process_objects: Dict[int, subprocess.Popen] = {}
process_lock = threading.Lock()

# 模板目录
templates_dir = project_root / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# MediaCrawler路径
MEDIACRAWLER_PATH = project_root / "MediaCrawler"

# 平台映射（Web界面显示名称）
PLATFORM_MAP = {
    "xhs": "小红书",
    "douyin": "抖音",
    "weibo": "微博",
    "zhihu": "知乎",
    "bilibili": "B站",
    "kuaishou": "快手",
    "tieba": "百度贴吧",
}

# MediaCrawler平台代码映射（MediaCrawler使用的代码）
MEDIACRAWLER_PLATFORM_MAP = {
    "xhs": "xhs",        # 小红书
    "douyin": "dy",      # 抖音
    "weibo": "wb",       # 微博
    "zhihu": "zhihu",    # 知乎
    "bilibili": "bili",  # B站（MediaCrawler使用bili作为目录名）
    "bili": "bili",      # B站（兼容直接使用bili）
    "kuaishou": "ks",    # 快手
    "tieba": "tieba",    # 百度贴吧
}

# MediaCrawler实际数据目录名映射（MediaCrawler在data目录下使用的实际目录名）
# 注意：命令行参数和数据目录名可能不一致！
# 命令行参数 -> 实际数据目录名
MEDIACRAWLER_DATA_DIR_MAP = {
    "xhs": "xhs",              # 小红书：命令行和目录都是xhs
    "douyin": "douyin",        # 抖音：命令行用dy，但数据目录是douyin
    "weibo": "weibo",          # 微博：命令行用wb，但数据目录是weibo
    "zhihu": "zhihu",          # 知乎：命令行和目录都是zhihu
    "bilibili": "bili",        # B站：命令行用bili，数据目录也是bili
    "bili": "bili",            # B站（兼容直接使用bili）
    "kuaishou": "kuaishou",    # 快手：命令行用ks，但数据目录是kuaishou
    "ks": "kuaishou",          # 快手（兼容ks代码）
    "tieba": "tieba",          # 百度贴吧：命令行和目录都是tieba
}

# 检查实际存在的目录名（用于兼容性）
def get_actual_data_dir(mediacrawler_path: Path, platform_code: str) -> Path:
    """
    获取实际的数据目录（检查可能的目录名变体）
    
    Args:
        mediacrawler_path: MediaCrawler根目录
        platform_code: 平台代码（可能是命令行参数或用户界面代码）
    
    Returns:
        实际的数据目录路径
    """
    base_dir = mediacrawler_path / "data"
    
    # 首先尝试标准映射（从用户界面代码或命令行参数映射到实际目录名）
    actual_dir_name = MEDIACRAWLER_DATA_DIR_MAP.get(platform_code, platform_code)
    standard_dir = base_dir / actual_dir_name
    
    # 如果标准目录存在，直接返回
    if standard_dir.exists():
        return standard_dir
    
    # 如果标准目录不存在，尝试其他可能的目录名（向后兼容）
    # 这种情况应该很少发生，因为我们已经修正了映射
    alt_names = {
        "ks": "kuaishou",
        "dy": "douyin",
        "wb": "weibo",
    }
    
    if platform_code in alt_names:
        alt_dir = base_dir / alt_names[platform_code]
        if alt_dir.exists():
            return alt_dir
    
    # 返回标准目录（即使不存在，让调用者处理）
    return standard_dir

def sync_media_files_for_platform(platform: str):
    """
    同步指定平台的媒体文件到项目数据目录
    
    Args:
        platform: 平台代码 (如 xhs, douyin)
    """
    if not settings.MEDIACRAWLER_PATH:
        logger.warning("未配置 MEDIACRAWLER_PATH，无法同步媒体文件")
        return
        
    mediacrawler_path = Path(settings.MEDIACRAWLER_PATH)
    if not mediacrawler_path.is_absolute():
        mediacrawler_path = (project_root / settings.MEDIACRAWLER_PATH).resolve()
        
    source_dir = mediacrawler_path / "data" / "crawled_data"
    target_dir = settings.DATA_DIR / "crawled_data"
    
    if not source_dir.exists():
        logger.warning(f"MediaCrawler 数据目录不存在: {source_dir}")
        return
        
    # 获取实际的目录名 (platform 可能和目录名不一致)
    # 比如 platform 是 'dy'，但目录名是 'douyin'
    # 先尝试直接匹配
    platform_dir = source_dir / platform
    if not platform_dir.exists():
        # 尝试映射
        mapped_name = MEDIACRAWLER_DATA_DIR_MAP.get(platform)
        if mapped_name:
            platform_dir = source_dir / mapped_name
            
        # 如果还没找到，尝试特定映射
        if not platform_dir.exists():
            if platform == 'dy': platform_dir = source_dir / 'douyin'
            elif platform == 'ks': platform_dir = source_dir / 'kuaishou'
            elif platform == 'wb': platform_dir = source_dir / 'weibo'
            elif platform == 'bili': platform_dir = source_dir / 'bilibili'
            
    if not platform_dir.exists():
        logger.warning(f"未找到平台 {platform} 的数据目录: {platform_dir}")
        return
        
    platform_name = platform_dir.name # 使用实际存在的目录名
    
    content_dirs = [d for d in platform_dir.iterdir() if d.is_dir()]
    logger.info(f"正在同步平台 {platform_name} 的文件，发现 {len(content_dirs)} 个内容目录")
    
    count = 0
    for content_dir in content_dirs:
        content_id = content_dir.name
        
        # 构建目标目录
        target_content_dir = target_dir / platform_name / content_id
        target_content_dir.mkdir(parents=True, exist_ok=True)
        
        # 复制文件
        for file_path in content_dir.iterdir():
            if file_path.is_file():
                target_file = target_content_dir / file_path.name
                
                should_copy = False
                if not target_file.exists():
                    should_copy = True
                elif target_file.stat().st_size != file_path.stat().st_size:
                    should_copy = True
                    
                if should_copy:
                    try:
                        shutil.copy2(file_path, target_file)
                        count += 1
                    except Exception as e:
                        logger.warning(f"复制文件失败 {file_path}: {e}")
                        
    logger.info(f"同步完成，共复制 {count} 个文件")

# 平台特性配置
PLATFORM_FEATURES = {
    "xhs": {
        "supports_note_type": True,   # 支持笔记类型选择
        "supports_comments": True,    # 支持评论
    },
    "douyin": {
        "supports_note_type": True,   # 支持笔记类型选择 (实测支持 video/image)
        "supports_comments": True,
    },
    "weibo": {
        "supports_note_type": False,
        "supports_comments": True,
    },
    "zhihu": {
        "supports_note_type": False,
        "supports_comments": True,
    },
    "bilibili": {
        "supports_note_type": False,
        "supports_comments": True,
    },
    "kuaishou": {
        "supports_note_type": True,   # 快手也支持视频/图文
        "supports_comments": True,
    },
    "tieba": {
        "supports_note_type": False,
        "supports_comments": True,
    },
}

# 笔记类型映射
NOTE_TYPE_MAP = {
    "all": "全部",
    "video": "视频",
    "image": "图文",
}


def set_max_count(mediacrawler_path: Path, max_count: int) -> bool:
    """设置配置文件中的最大爬取数量"""
    config_file = mediacrawler_path / "config" / "base_config.py"
    if not config_file.exists():
        return False
    
    try:
        # 读取配置文件
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 备份原配置
        backup_file = config_file.with_suffix('.py.bak')
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 替换 CRAWLER_MAX_NOTES_COUNT
        pattern = r'CRAWLER_MAX_NOTES_COUNT\s*=\s*\d+'
        replacement = f'CRAWLER_MAX_NOTES_COUNT = {max_count}'
        new_content = re.sub(pattern, replacement, content)
        
        # 写入新配置
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
    except Exception as e:
        logger.error(f"修改配置失败: {e}")
        return False


def restore_config(mediacrawler_path: Path):
    """恢复配置文件"""
    config_file = mediacrawler_path / "config" / "base_config.py"
    backup_file = config_file.with_suffix('.py.bak')
    
    if backup_file.exists():
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(content)
            backup_file.unlink()
        except Exception:
            pass


@router.get("/mediacrawler", response_class=HTMLResponse)
async def mediacrawler_ui(request: Request):
    """MediaCrawler爬虫界面"""
    platforms = [
        {"code": code, "name": name}
        for code, name in PLATFORM_MAP.items()
    ]
    return templates.TemplateResponse("mediacrawler_ui.html", {
        "request": request,
        "platforms": platforms,
        "note_types": [
            {"code": "all", "name": "全部"},
            {"code": "video", "name": "视频"},
            {"code": "image", "name": "图文"},
        ]
    })


@router.post("/mediacrawler/start")
async def start_mediacrawler(
    request: Request
):
    """启动MediaCrawler爬取任务（支持多平台）"""
    try:
        # 直接从请求中获取表单数据，避免FastAPI的Form参数验证问题
        form_data = await request.form()
        
        # 记录所有接收到的表单字段（用于调试）
        logger.info(f"接收到的表单字段: {list(form_data.keys())}")
        for key, value in form_data.items():
            logger.info(f"  {key} = {value}")
        
        # 获取参数
        platforms = form_data.get("platforms", "")
        platform = form_data.get("platform", "")
        keywords = form_data.get("keywords", "").strip()
        
        crawl_type = form_data.get("crawl_type", "search")
        target_url = form_data.get("target_url", "").strip()
        
        # 安全地转换max_items
        try:
            max_items = int(form_data.get("max_items", 10))
        except (ValueError, TypeError):
            max_items = 10
        
        note_type = form_data.get("note_type", "all")
        include_comments = form_data.get("include_comments", "false")
        include_sub_comments = form_data.get("include_sub_comments", "false")
    except Exception as e:
        logger.error(f"解析表单数据失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"解析表单数据失败: {str(e)}"
        )
    
    # 验证必填参数
    if crawl_type == "search" and not keywords:
        raise HTTPException(
            status_code=400,
            detail="关键词（keywords）不能为空"
        )
    
    if crawl_type in ["creator", "detail"] and not target_url:
        raise HTTPException(
            status_code=400,
            detail="目标URL（target_url）不能为空"
        )
    
    # 记录接收到的参数（用于调试）
    logger.info(f"收到请求参数: platforms={platforms}, platform={platform}, keywords={keywords}, crawl_type={crawl_type}, target_url={target_url}")
    
    # 解析平台列表：优先使用platforms，如果没有则使用platform（兼容旧版本）
    platform_str = (platforms or platform or "").strip()
    if not platform_str:
        logger.error(f"平台参数为空: platforms={platforms}, platform={platform}")
        raise HTTPException(
            status_code=400,
            detail="请至少选择一个平台（platforms参数不能为空）"
        )
    
    platform_list = [p.strip() for p in platform_str.split(",") if p.strip()]
    
    if not platform_list:
        logger.error(f"解析后的平台列表为空: platform_str={platform_str}")
        return JSONResponse({
            "success": False,
            "error": "请至少选择一个平台"
        })
    
    # 转换布尔值参数
    include_comments_bool = include_comments.lower() in ('true', '1', 'yes', 'on')
    include_sub_comments_bool = include_sub_comments.lower() in ('true', '1', 'yes', 'on')
    
    logger.info(f"收到爬取请求: platforms={platform_list}, keywords={keywords}, max_items={max_items}")
    logger.info(f"参数详情: include_comments={include_comments}->{include_comments_bool}, include_sub_comments={include_sub_comments}->{include_sub_comments_bool}")
    
    # 验证平台
    invalid_platforms = [p for p in platform_list if p not in PLATFORM_MAP]
    if invalid_platforms:
        return JSONResponse({
            "success": False,
            "error": f"无效的平台: {', '.join(invalid_platforms)}"
        })
    
    # 验证笔记类型
    if note_type not in NOTE_TYPE_MAP:
        return JSONResponse({
            "success": False,
            "error": f"无效的笔记类型: {note_type}"
        })
    
    # 验证关键词/URL
    if crawl_type == "search" and not keywords.strip():
        return JSONResponse({
            "success": False,
            "error": "关键词不能为空"
        })
    
    if crawl_type in ["creator", "detail"] and not target_url.strip():
        return JSONResponse({
            "success": False,
            "error": "目标URL不能为空"
        })
    
    # 检查MediaCrawler目录
    if not MEDIACRAWLER_PATH.exists():
        return JSONResponse({
            "success": False,
            "error": "MediaCrawler目录不存在"
        })
    
    main_py = MEDIACRAWLER_PATH / "main.py"
    if not main_py.exists():
        return JSONResponse({
            "success": False,
            "error": "未找到MediaCrawler的main.py"
        })
    
    # 设置最大爬取数量
    if not set_max_count(MEDIACRAWLER_PATH, max_items):
        logger.warning("无法设置最大数量，将使用配置文件中的默认值")
    
    # Python命令
    python_cmd = "python"
    python_env = MEDIACRAWLER_PATH / "python_env" / "python.exe"
    if python_env.exists():
        python_cmd = str(python_env.resolve())
    
    # 工作目录
    work_dir = str(MEDIACRAWLER_PATH.resolve())
    
    # 设置环境变量，确保UTF-8编码（Windows）
    env = os.environ.copy()
    if sys.platform == 'win32':
        env['PYTHONIOENCODING'] = 'utf-8'
    
    # 为每个平台创建独立的进程
    process_ids = []
    script_generator = ScriptGenerator(MEDIACRAWLER_PATH)
    
    try:
        for platform in platform_list:
            # 获取MediaCrawler平台代码
            mediacrawler_platform = MEDIACRAWLER_PLATFORM_MAP.get(platform, platform)
            
            # 获取平台特性
            features = PLATFORM_FEATURES.get(platform, {})
            
            # 如果平台不支持笔记类型，使用默认值
            platform_note_type = note_type
            if not features.get("supports_note_type", False):
                platform_note_type = "all"
            
            try:
                # 生成独立的爬取脚本
                script_path = script_generator.generate_script(
                    platform=platform,
                    keywords=keywords,
                    max_items=max_items,
                    note_type=platform_note_type,
                    include_comments=include_comments_bool,
                    include_sub_comments=include_sub_comments_bool,
                    crawl_type=crawl_type,
                    target_url=target_url
                )
                
                # 验证脚本文件是否存在
                if not script_path.exists():
                    logger.error(f"生成的脚本文件不存在: {script_path}")
                    continue
                
                logger.info(f"已生成爬取脚本: {script_path}")
                logger.info(f"平台: {platform}, 关键词: {keywords}, 最大数量: {max_items}")
                
                # 使用生成的脚本文件
                cmd = [
                    python_cmd,
                    str(script_path.resolve())
                ]
                
                # 如果不是第一个任务，添加延时以避免资源竞争（特别是启动浏览器时）
                if process_ids:
                    logger.info("等待 3 秒后启动下一个任务，以避免资源竞争...")
                    time.sleep(3)
                
                # 执行命令（异步执行，不阻塞）
                logger.info(f"执行命令: {' '.join(cmd)}")
                logger.info(f"工作目录: {work_dir}")
                logger.info(f"脚本路径: {script_path}")
                
                process = subprocess.Popen(
                    cmd,
                    cwd=work_dir,
                    stdout=subprocess.PIPE,  # 捕获标准输出
                    stderr=subprocess.STDOUT,  # 将错误输出合并到标准输出
                    bufsize=1,  # 行缓冲
                    env=env  # 使用修改后的环境变量
                )
                
                logger.info(f"进程已创建，PID: {process.pid}")
                
                # 初始化进程输出存储和进程对象存储
                process_id = process.pid
                process_ids.append(process_id)
                logger.info(f"进程已启动，进程ID: {process_id}")
                logger.info(f"使用脚本: {script_path}")
                
                with process_lock:
                    process_outputs[process_id] = {
                        "status": "running",
                        "output": [],
                        "qrcode_url": None,
                        "started_at": datetime.now().isoformat(),
                        "platform": platform,
                        "platforms": platform_list,  # 保存所有平台列表
                        "keywords": keywords,
                        "crawl_type": crawl_type,
                        "target_url": target_url,
                        "max_items": max_items,
                        "script_path": str(script_path)  # 保存脚本路径
                    }
                    process_objects[process_id] = process
                    logger.info(f"进程数据已存储，process_outputs中的进程ID: {list(process_outputs.keys())}")
                    
                    # 为每个进程启动独立的输出读取线程
                    def read_output_for_process(proc, proc_id, plat):
                        """读取进程输出的线程函数"""
                        qrcode_pattern = re.compile(r'https?://[^\s]+\.(?:png|jpg|jpeg|gif)', re.IGNORECASE)
                        path_pattern = re.compile(r'[A-Za-z]:[\\/][^\s<>"|?*]+\.(?:png|jpg|jpeg|gif)', re.IGNORECASE)
                        
                        try:
                            logger.info(f"[进程{proc_id}] 开始读取输出...")
                            
                            with process_lock:
                                if proc_id in process_outputs:
                                    process_outputs[proc_id]["output"].append({
                                        "text": f"进程已启动，开始读取输出...",
                                        "type": "info",
                                        "timestamp": datetime.now().isoformat()
                                    })
                            
                            try:
                                while True:
                                    if proc.poll() is not None:
                                        logger.info(f"[进程{proc_id}] 进程已结束，返回码: {proc.returncode}")
                                        break
                                    
                                    try:
                                        line_bytes = proc.stdout.readline()
                                        if not line_bytes:
                                            time.sleep(0.1)
                                            continue
                                        # 手动解码，处理可能的编码错误
                                        try:
                                            line = line_bytes.decode('utf-8')
                                        except UnicodeDecodeError:
                                            try:
                                                line = line_bytes.decode('gbk')
                                            except UnicodeDecodeError:
                                                line = line_bytes.decode('utf-8', errors='replace')
                                                
                                    except (ValueError, OSError) as e:
                                        logger.debug(f"[进程{proc_id}] 读取输出时出错: {e}")
                                        if proc.poll() is not None:
                                            break
                                        time.sleep(0.1)
                                        continue
                                    
                                    line = line.strip()
                                    if not line:
                                        continue
                                    
                                    logger.debug(f"[进程{proc_id}] 输出: {line[:100]}")
                                    
                                    output_type = "info"
                                    if "ERROR" in line or "错误" in line or "失败" in line:
                                        output_type = "error"
                                    elif "WARNING" in line or "警告" in line:
                                        output_type = "warning"
                                    elif "成功" in line or "完成" in line or "SUCCESS" in line:
                                        output_type = "success"
                                    
                                    qrcode_match = qrcode_pattern.search(line)
                                    if qrcode_match:
                                        qrcode_url = qrcode_match.group(0)
                                        with process_lock:
                                            if proc_id in process_outputs:
                                                process_outputs[proc_id]["qrcode_url"] = qrcode_url
                                    
                                    if "qrcode" in line.lower() or "二维码" in line:
                                        path_matches = path_pattern.findall(line)
                                        for qrcode_path_str in path_matches:
                                            try:
                                                qrcode_path = Path(qrcode_path_str)
                                                if qrcode_path.exists() and qrcode_path.is_file():
                                                    try:
                                                        rel_path = qrcode_path.relative_to(MEDIACRAWLER_PATH)
                                                        qrcode_url = f"/api/v1/mediacrawler/qrcode/{rel_path.as_posix().replace(chr(92), '/')}"
                                                        with process_lock:
                                                            if proc_id in process_outputs:
                                                                process_outputs[proc_id]["qrcode_url"] = qrcode_url
                                                        break
                                                    except ValueError:
                                                        pass
                                            except Exception:
                                                pass
                                    
                                    with process_lock:
                                        if proc_id in process_outputs:
                                            process_outputs[proc_id]["output"].append({
                                                "text": line,
                                                "type": output_type,
                                                "timestamp": datetime.now().isoformat()
                                            })
                                    
                                    logger.info(f"[进程{proc_id}] {line}")
                            except Exception as e:
                                logger.error(f"[进程{proc_id}] 读取输出时发生异常: {e}", exc_info=True)
                            
                            returncode = proc.wait()
                            logger.info(f"[进程{proc_id}] 进程已结束，返回码: {returncode}")
                            
                            # 任务成功结束后，自动同步媒体文件
                            if returncode == 0:
                                try:
                                    logger.info(f"[进程{proc_id}] 开始同步媒体文件...")
                                    sync_media_files_for_platform(plat)
                                    logger.info(f"[进程{proc_id}] 媒体文件同步完成")
                                except Exception as e:
                                    logger.error(f"[进程{proc_id}] 同步媒体文件失败: {e}")
                            
                            with process_lock:
                                if proc_id in process_outputs:
                                    current_status = process_outputs[proc_id].get("status")
                                    if current_status != "stopped":
                                        if returncode == 0:
                                            process_outputs[proc_id]["status"] = "completed"
                                        else:
                                            process_outputs[proc_id]["status"] = "failed"
                                    process_outputs[proc_id]["completed_at"] = datetime.now().isoformat()
                                    process_outputs[proc_id]["returncode"] = returncode
                                if proc_id in process_objects:
                                    del process_objects[proc_id]
                        except Exception as e:
                            logger.error(f"读取进程输出失败: {e}")
                            with process_lock:
                                if proc_id in process_outputs:
                                    process_outputs[proc_id]["status"] = "failed"
                                    process_outputs[proc_id]["error"] = str(e)
                    
                    # 启动输出读取线程
                    output_thread = threading.Thread(
                        target=read_output_for_process,
                        args=(process, process_id, platform),
                        daemon=True
                    )
                    output_thread.start()
                    logger.info(f"已为平台 {platform} 启动输出读取线程，进程ID: {process_id}")
            except Exception as e:
                logger.error(f"启动平台 {platform} 的爬取任务失败: {e}", exc_info=True)
                continue
        
        if not process_ids:
            restore_config(MEDIACRAWLER_PATH)
            return JSONResponse({
                "success": False,
                "error": "未能启动任何爬取任务"
            }, status_code=500)
        
        logger.info(f"启动爬取任务: platforms={platform_list}, keywords={keywords}, max_items={max_items}, type={crawl_type}")
        logger.info(f"进程ID列表: {process_ids}")
        logger.info(f"提示: MediaCrawler会在浏览器中打开登录页面，二维码显示在浏览器中，不会弹出窗口")
        logger.info(f"提示: 登录状态会自动保存（SAVE_LOGIN_STATE=True），下次不需要重复登录")
        
        # 返回多个进程的信息
        platform_names = [PLATFORM_MAP.get(p, p) for p in platform_list]
        
        return JSONResponse({
            "success": True,
            "message": f"已启动 {len(process_ids)} 个爬取任务",
            "platforms": platform_list,
            "platform_names": platform_names,
            "keywords": keywords,
            "crawl_type": crawl_type,
            "target_url": target_url,
            "max_items": max_items,
            "note_type": note_type,
            "include_comments": include_comments_bool,
            "include_sub_comments": include_sub_comments_bool,
            "process_ids": process_ids,
            "monitor_urls": [f"/api/v1/mediacrawler/crawl/monitor/{pid}" for pid in process_ids]
        })
        
    except subprocess.SubprocessError as e:
        logger.error(f"启动子进程失败: {e}", exc_info=True)
        restore_config(MEDIACRAWLER_PATH)
        return JSONResponse({
            "success": False,
            "error": f"启动爬取任务失败: 子进程错误 - {str(e)}"
        }, status_code=500)
    except FileNotFoundError as e:
        logger.error(f"文件未找到: {e}", exc_info=True)
        restore_config(MEDIACRAWLER_PATH)
        return JSONResponse({
            "success": False,
            "error": f"启动爬取任务失败: 文件未找到 - {str(e)}"
        }, status_code=500)
    except Exception as e:
        logger.error(f"启动爬取任务失败: {e}", exc_info=True)
        restore_config(MEDIACRAWLER_PATH)
        return JSONResponse({
            "success": False,
            "error": f"启动爬取任务失败: {str(e)}"
        }, status_code=500)


@router.get("/mediacrawler/monitor", response_class=HTMLResponse)
async def monitor_dashboard(request: Request):
    """任务监控看板"""
    # 整理进程数据
    processes_info = {}
    with process_lock:
        # 按时间倒序排列
        sorted_pids = sorted(
            process_outputs.keys(), 
            key=lambda pid: process_outputs[pid].get("started_at", ""), 
            reverse=True
        )
        
        for pid in sorted_pids:
            p_data = process_outputs[pid]
            platform_code = p_data.get("platform", "unknown")
            processes_info[pid] = {
                "status": p_data.get("status", "unknown"),
                "platform": platform_code,
                "platform_name": PLATFORM_MAP.get(platform_code, platform_code),
                "keywords": p_data.get("keywords", ""),
                "started_at": p_data.get("started_at", ""),
                "max_items": p_data.get("max_items", 0)
            }
            
    return templates.TemplateResponse("monitor_dashboard.html", {
        "request": request,
        "processes": processes_info
    })


@router.get("/mediacrawler/processes")
async def get_processes():
    """获取所有进程列表（API）"""
    processes_list = []
    with process_lock:
        sorted_pids = sorted(
            process_outputs.keys(), 
            key=lambda pid: process_outputs[pid].get("started_at", ""), 
            reverse=True
        )
        
        for pid in sorted_pids:
            p_data = process_outputs[pid]
            platform_code = p_data.get("platform", "unknown")
            processes_list.append({
                "process_id": pid,
                "status": p_data.get("status", "unknown"),
                "platform": platform_code,
                "platform_name": PLATFORM_MAP.get(platform_code, platform_code),
                "keywords": p_data.get("keywords", ""),
                "started_at": p_data.get("started_at", ""),
                "monitor_url": f"/api/v1/mediacrawler/crawl/monitor/{pid}"
            })
            
    return JSONResponse({
        "success": True,
        "processes": processes_list
    })


@router.get("/mediacrawler/crawl/monitor/{process_id}", response_class=HTMLResponse)
async def crawl_monitor_page(
    request: Request,
    process_id: int
):
    """爬取监控页面"""
    with process_lock:
        process_data = process_outputs.get(process_id)
    
    if not process_data:
        return HTMLResponse("<h1>进程不存在或已结束</h1>", status_code=404)
    
    platform = process_data.get("platform", "unknown")
    platform_name = PLATFORM_MAP.get(platform, platform)
    
    return templates.TemplateResponse("crawl_monitor.html", {
        "request": request,
        "process_id": process_id,
        "platform": platform,
        "platform_name": platform_name,
        "keywords": process_data.get("keywords", ""),
        "max_items": process_data.get("max_items", 0)
    })


@router.get("/mediacrawler/crawl/output/{process_id}")
async def get_crawl_output(process_id: int):
    """获取爬取输出"""
    logger.debug(f"获取进程输出请求: process_id={process_id}")
    
    with process_lock:
        process_data = process_outputs.get(process_id)
        current_process_ids = list(process_outputs.keys())
    
    if not process_data:
        logger.warning(f"进程不存在: process_id={process_id}, 当前进程ID列表: {current_process_ids}")
        return JSONResponse({
            "success": False,
            "error": f"进程不存在或已结束 (进程ID: {process_id})",
            "current_process_ids": current_process_ids
        }, status_code=404)
    
    return JSONResponse({
        "success": True,
        "data": {
            "status": process_data.get("status", "unknown"),
            "output": process_data.get("output", []),
            "qrcode_url": process_data.get("qrcode_url"),
            "started_at": process_data.get("started_at"),
            "completed_at": process_data.get("completed_at"),
            "returncode": process_data.get("returncode")
        }
    })


@router.post("/mediacrawler/crawl/stop/{process_id}")
async def stop_crawl(process_id: int):
    """停止爬取任务"""
    with process_lock:
        process = process_objects.get(process_id)
        process_data = process_outputs.get(process_id)
    
    if not process_data:
        return JSONResponse({
            "success": False,
            "error": "进程不存在或已结束"
        }, status_code=404)
    
    if process_data.get("status") in ["completed", "failed", "stopped"]:
        return JSONResponse({
            "success": False,
            "error": f"进程已结束，状态: {process_data.get('status')}"
        })
    
    try:
        # 终止进程
        if process and process.poll() is None:  # 进程仍在运行
            if os.name == 'nt':  # Windows
                # Windows下需要终止进程树
                try:
                    import psutil
                    parent = psutil.Process(process.pid)
                    children = parent.children(recursive=True)
                    for child in children:
                        child.terminate()
                    parent.terminate()
                    # 等待进程结束
                    gone, still_alive = psutil.wait_procs(children + [parent], timeout=5)
                    for p in still_alive:
                        p.kill()
                except ImportError:
                    # 如果没有psutil，尝试直接terminate
                    logger.warning("psutil未安装，使用基本terminate方法")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                except Exception as e:
                    logger.warning(f"使用psutil终止进程失败: {e}，尝试直接terminate")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
            else:  # Linux/Mac
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            
            # 更新状态
            with process_lock:
                if process_id in process_outputs:
                    process_outputs[process_id]["status"] = "stopped"
                    process_outputs[process_id]["stopped_at"] = datetime.now().isoformat()
                    process_outputs[process_id]["output"].append({
                        "text": "用户手动停止爬取任务",
                        "type": "warning",
                        "timestamp": datetime.now().isoformat()
                    })
                if process_id in process_objects:
                    del process_objects[process_id]
            
            logger.info(f"已停止爬取任务，进程ID: {process_id}")
            
            return JSONResponse({
                "success": True,
                "message": "爬取任务已停止",
                "process_id": process_id
            })
        else:
            # 进程已经结束
            with process_lock:
                if process_id in process_outputs:
                    process_outputs[process_id]["status"] = "stopped"
                if process_id in process_objects:
                    del process_objects[process_id]
            
            return JSONResponse({
                "success": True,
                "message": "进程已结束",
                "process_id": process_id
            })
            
    except Exception as e:
        logger.error(f"停止爬取任务失败: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": f"停止任务失败: {str(e)}"
        }, status_code=500)


@router.get("/mediacrawler/qrcode/{file_path:path}")
async def get_qrcode_image(file_path: str):
    """获取二维码图片"""
    qrcode_path = MEDIACRAWLER_PATH / file_path
    if not qrcode_path.exists() or not qrcode_path.is_file():
        return JSONResponse({
            "success": False,
            "error": "二维码文件不存在"
        }, status_code=404)
    
    from fastapi.responses import FileResponse
    return FileResponse(
        qrcode_path,
        media_type="image/png",
        filename=qrcode_path.name
    )


@router.get("/mediacrawler/data", response_class=HTMLResponse)
async def view_json_data(
    request: Request,
    platform: Optional[str] = Query(None, description="平台代码（可选，用于兼容旧链接）"),
    data_type: str = Query("contents", description="数据类型: contents或comments")
):
    """查看JSON数据页面（支持多平台筛选）"""
    # 传递所有平台信息给前端
    platforms_list = [{"code": code, "name": name} for code, name in PLATFORM_MAP.items()]
    
    return templates.TemplateResponse("json_data_viewer.html", {
        "request": request,
        "platform": platform,  # 保留用于兼容
        "platform_name": PLATFORM_MAP.get(platform, "全部平台") if platform else "全部平台",
        "data_type": data_type,
        "platforms": platforms_list
    })


@router.get("/mediacrawler/data/list")
async def list_json_files(
    platforms: Optional[str] = Query(None, description="平台代码列表，逗号分隔，如: xhs,douyin"),
    data_type: str = Query("contents", description="数据类型: contents或comments"),
    keyword: Optional[str] = Query(None, description="关键词筛选（在文件名中搜索）")
):
    """获取JSON文件列表（支持多平台筛选）"""
    # 解析平台列表
    platform_list = []
    if platforms:
        platform_list = [p.strip() for p in platforms.split(",") if p.strip()]
        # 验证平台代码
        invalid_platforms = [p for p in platform_list if p not in PLATFORM_MAP]
        if invalid_platforms:
            return JSONResponse({
                "success": False,
                "error": f"无效的平台代码: {', '.join(invalid_platforms)}"
            }, status_code=400)
    
    # 如果没有指定平台，获取所有平台
    if not platform_list:
        platform_list = list(PLATFORM_MAP.keys())
    
    all_files = []
    
    # 遍历所有选中的平台
    for platform in platform_list:
        # 使用实际的数据目录名（MediaCrawler可能使用不同的目录名）
        actual_dir_name = MEDIACRAWLER_DATA_DIR_MAP.get(platform, platform)
        # 检查实际存在的目录
        actual_data_dir = get_actual_data_dir(MEDIACRAWLER_PATH, platform)
        data_dir = actual_data_dir / "json"
        
        if not data_dir.exists():
            continue
        
        # 查找JSON文件 (兼容旧格式 search_xxx 和新格式 platform_keyword_xxx)
        # 旧格式: search_contents_xxx.json
        # 新格式: xhs_keyword_contents_xxx.json
        # 通用匹配: *_{data_type}_*.json
        if data_type == "all":
            pattern = "*.json"
        else:
            pattern = f"*_{data_type}_*.json"
            
        json_files = list(data_dir.glob(pattern))
        
        for file_path in sorted(json_files, key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                # 关键词筛选
                if keyword and keyword.lower() not in file_path.name.lower():
                    continue
                
                stat = file_path.stat()
                all_files.append({
                    "filename": file_path.name,
                    "size": stat.st_size,
                    "modified_time": stat.st_mtime,
                    "path": str(file_path.relative_to(MEDIACRAWLER_PATH)),
                    "platform": platform,  # 使用原始平台代码（用于API返回）
                    "platform_name": PLATFORM_MAP.get(platform, platform),
                    "actual_dir": actual_dir_name  # 实际目录名（用于调试）
                })
            except Exception as e:
                logger.error(f"读取文件信息失败: {e}")
    
    # 按修改时间排序
    all_files.sort(key=lambda x: x["modified_time"], reverse=True)
    
    # 记录日志
    logger.info(f"获取文件列表: 平台={platform_list}, 数据类型={data_type}, 关键词={keyword}, 找到{len(all_files)}个文件")
    
    return JSONResponse({
        "success": True,
        "files": all_files,
        "platforms": platform_list,
        "data_type": data_type,
        "keyword": keyword,
        "total": len(all_files)
    })


@router.get("/mediacrawler/data/file")
async def get_json_file_content(
    platform: str = Query(..., description="平台代码"),
    filename: str = Query(..., description="文件名"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词筛选（在内容中搜索）")
):
    """获取JSON文件内容（分页，支持关键词筛选）"""
    if platform not in PLATFORM_MAP:
        return JSONResponse({
            "success": False,
            "error": "无效的平台"
        }, status_code=400)
    
    # 使用实际的数据目录名（检查实际存在的目录）
    actual_data_dir = get_actual_data_dir(MEDIACRAWLER_PATH, platform)
    file_path = actual_data_dir / "json" / filename
    
    if not file_path.exists():
        return JSONResponse({
            "success": False,
            "error": "文件不存在"
        }, status_code=404)
    
    try:
        # 读取JSON文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 确保是列表
        if not isinstance(data, list):
            data = [data]
        
        # 关键词筛选
        if keyword:
            keyword_lower = keyword.lower()
            filtered_data = []
            for item in data:
                # 将整个item转换为字符串进行搜索
                item_str = json.dumps(item, ensure_ascii=False).lower()
                if keyword_lower in item_str:
                    filtered_data.append(item)
            data = filtered_data
        
        # 分页
        total = len(data)
        start = (page - 1) * page_size
        end = start + page_size
        items = data[start:end]
        
        return JSONResponse({
            "success": True,
            "data": {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "filename": filename,
                "platform": platform
            }
        })
        
    except json.JSONDecodeError as e:
        return JSONResponse({
            "success": False,
            "error": f"JSON解析失败: {str(e)}"
        }, status_code=400)
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        return JSONResponse({
            "success": False,
            "error": f"读取文件失败: {str(e)}"
        }, status_code=500)


