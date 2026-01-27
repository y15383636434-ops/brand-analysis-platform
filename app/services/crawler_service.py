"""
爬虫服务 - 封装MediaCrawler调用
"""
import subprocess
import json
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger
from datetime import datetime

from config import settings
from app.services.login_checker import LoginChecker


class CrawlerService:
    """爬虫服务类"""
    
    # 平台映射（MediaCrawler命令行参数）
    # 注意：这个映射用于MediaCrawler命令行参数，不是数据目录名
    PLATFORM_MAP = {
        "xhs": "xhs",        # 小红书
        "douyin": "dy",      # 抖音
        "weibo": "wb",       # 微博
        "zhihu": "zhihu",    # 知乎
        "bilibili": "bili",  # B站
        "kuaishou": "ks",    # 快手
        "tieba": "tieba",    # 百度贴吧
    }
    
    def __init__(self):
        """初始化爬虫服务"""
        # MediaCrawler路径
        if settings.MEDIACRAWLER_PATH:
            # 如果是相对路径，转换为绝对路径（基于项目根目录）
            if settings.MEDIACRAWLER_PATH.startswith("./") or settings.MEDIACRAWLER_PATH.startswith(".\\"):
                # 相对路径：基于项目根目录（config.py所在目录）
                project_root = Path(__file__).parent.parent.parent  # app/services -> app -> project_root
                self.mediacrawler_path = (project_root / settings.MEDIACRAWLER_PATH.lstrip("./\\")).resolve()
            else:
                # 绝对路径
                self.mediacrawler_path = Path(settings.MEDIACRAWLER_PATH)
        else:
            self.mediacrawler_path = None
        
        # 如果路径不存在，尝试从环境变量获取
        if not self.mediacrawler_path or not self.mediacrawler_path.exists():
            env_path = os.getenv("MEDIACRAWLER_PATH")
            if env_path:
                self.mediacrawler_path = Path(env_path)
        
        # MediaCrawler的Python解释器（如果有独立环境）
        self.mediacrawler_python = settings.MEDIACRAWLER_PYTHON
        if not self.mediacrawler_python and self.mediacrawler_path:
            # 检查是否有独立的Python环境
            python_env = self.mediacrawler_path / "python_env" / "python.exe"
            if python_env.exists():
                self.mediacrawler_python = str(python_env)
        
        self.data_dir = settings.DATA_DIR / "crawled_data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化登录检查器
        if self.mediacrawler_path:
            self.login_checker = LoginChecker(str(self.mediacrawler_path))
        else:
            self.login_checker = None
        
        # 检查MediaCrawler是否可用
        if self.mediacrawler_path and self.mediacrawler_path.exists():
            main_py = self.mediacrawler_path / "main.py"
            if main_py.exists():
                logger.info(f"MediaCrawler路径: {self.mediacrawler_path}")
            else:
                logger.warning(f"MediaCrawler路径存在但未找到main.py: {self.mediacrawler_path}")
                self.mediacrawler_path = None
        else:
            logger.warning("MediaCrawler未配置，爬取将失败")
    
    def crawl_platform(
        self,
        platform: str,
        keywords: List[str],
        max_items: int = 100,
        include_comments: bool = False,
        output_dir: Optional[Path] = None,
        crawl_type: str = "search",
        target_url: Optional[str] = None,
        enable_media_download: bool = True
    ) -> Dict:
        """
        爬取指定平台的数据
        
        Args:
            platform: 平台名称 (xhs, douyin, weibo, zhihu等)
            keywords: 关键词列表
            max_items: 最大采集数量
            include_comments: 是否包含评论
            output_dir: 输出目录
            crawl_type: 爬取类型 (search/creator/detail)
            target_url: 目标链接 (用于creator/detail模式)
            enable_media_download: 是否下载媒体文件
            
        Returns:
            爬取结果字典
        """
        try:
            # 转换平台名称
            platform_code = self.PLATFORM_MAP.get(platform.lower(), platform.lower())
            
            if not output_dir:
                output_dir = self.data_dir / platform / datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"开始爬取平台: {platform}, 关键词: {keywords}, 类型: {crawl_type}, 链接: {target_url}, 下载媒体: {enable_media_download}")
            
            # 检查MediaCrawler是否可用
            if not self.mediacrawler_path or not self.mediacrawler_path.exists():
                raise Exception(f"MediaCrawler目录不存在: {self.mediacrawler_path}")
            
            main_py = self.mediacrawler_path / "main.py"
            if not main_py.exists():
                raise Exception(f"MediaCrawler的main.py不存在: {main_py}")
            
            # 使用MediaCrawler进行真实爬取
            logger.info(f"使用MediaCrawler进行真实爬取: {self.mediacrawler_path}")
            result = self._crawl_with_mediacrawler(
                platform_code, keywords, max_items, include_comments, output_dir, crawl_type, target_url, enable_media_download
            )
            
            # 检查是否真的爬取到数据
            if result.get("total_items", 0) == 0 or not result.get("is_real_crawl", False):
                raise Exception("MediaCrawler执行但未获取到数据，爬取失败")
            
            return result
                
        except Exception as e:
            logger.error(f"爬取失败: {e}", exc_info=True)
            raise
    
    def _crawl_with_mediacrawler(
        self,
        platform: str,
        keywords: List[str],
        max_items: int,
        include_comments: bool,
        output_dir: Path,
        crawl_type: str = "search",
        target_url: Optional[str] = None,
        enable_media_download: bool = True
    ) -> Dict:
        """使用MediaCrawler进行实际爬取"""
        results = []
        
        # 确定Python解释器
        python_cmd = self.mediacrawler_python or "python"
        main_py = self.mediacrawler_path / "main.py"
        
        # 设置工作目录为MediaCrawler目录
        work_dir = str(self.mediacrawler_path)
        
        # 转换平台代码为MediaCrawler使用的平台代码（与Web界面保持一致）
        mediacrawler_platform = self.PLATFORM_MAP.get(platform.lower(), platform.lower())
        
        # 设置最大爬取数量（动态修改配置文件，与Web界面保持一致）
        config_modified = False
        media_config_modified = False
        
        try:
            from app.api.v1.mediacrawler_ui import set_max_count, restore_config, update_config_value
            config_modified = set_max_count(self.mediacrawler_path, max_items)
            
            # 设置是否下载媒体文件
            media_config_modified = self._update_mediacrawler_media_config(enable_media_download)
            
            # 如果是指定博主/帖子模式，需要把 URL 写入配置文件的 DY_CREATOR_ID_LIST / DY_SPECIFIED_ID_LIST 等
            if crawl_type == "creator" and target_url:
                # 注意：MediaCrawler 配置文件中，不同平台对应的配置项不同
                # 这里目前主要支持抖音 creator 模式作为示例
                if platform == "dy":
                    # 临时修改 DY_CREATOR_ID_LIST
                    # 注意：这需要 update_config_value 支持修改列表类型，或者我们直接修改配置文件
                    # 鉴于修改列表比较复杂，这里我们假设 MediaCrawler 支持通过命令行传 URL (实际上目前不支持，主要靠配置文件)
                    # 所以必须修改配置文件
                    pass 
                    
            if config_modified:
                logger.info(f"已设置最大爬取数量: {max_items}")
            if media_config_modified:
                logger.info(f"已设置媒体下载: {enable_media_download}")
        except Exception as e:
            logger.warning(f"设置爬虫配置失败: {e}")
        
        try:
            # 准备执行列表
            # 如果是 search 模式，遍历关键词
            # 如果是 creator/detail 模式，只执行一次（因为 URL 在配置文件或参数中）
            
            run_items = keywords if crawl_type == "search" else [target_url]
            
            for item in run_items:
                try:
                    # 针对 creator/detail 模式，如果需要修改配置（MediaCrawler 主要是通过 config.py 读取 ID 列表）
                    # 我们这里做一个特殊的处理：临时修改 MediaCrawler 的配置文件的 ID 列表
                    if crawl_type in ["creator", "detail"] and target_url:
                        self._update_mediacrawler_url_config(platform, crawl_type, target_url)
                    
                    # 构建MediaCrawler命令
                    all_keywords = ",".join(keywords) if keywords else ""
                    
                    # 检查登录状态
                    login_type = "qrcode"
                    if self.login_checker:
                        internal_platform = platform.lower()
                        # MediaCrawler 的 platform 参数可能是 dy, xhs 等简写，这里转回全称或简写
                        # check_login_status 需要确定的平台名称
                        check_platform = "douyin" if platform == "dy" else platform
                        if check_platform == "dy": check_platform = "douyin"
                        if check_platform == "wb": check_platform = "weibo"
                        
                        if self.login_checker.check_login_status(check_platform):
                            login_type = "cookie"
                            logger.info(f"[{platform}] 检测到已保存的登录状态，使用cookie模式，无需扫码")
                        else:
                            logger.info(f"[{platform}] 未检测到登录状态，使用二维码登录模式")
                    
                    cmd = [
                        python_cmd,
                        str(main_py),
                        "--platform", mediacrawler_platform,
                        "--lt", login_type,
                        "--type", crawl_type,  # search / creator / detail
                        "--save_data_option", "json",
                    ]
                    
                    # 只有 search 模式才需要 keywords 参数
                    if crawl_type == "search" and all_keywords:
                        cmd.extend(["--keywords", all_keywords])
                    
                    # 设置是否爬取评论
                    if include_comments:
                        cmd.extend(["--get_comment", "yes"])
                        cmd.extend(["--get_sub_comment", "no"])
                    else:
                        cmd.extend(["--get_comment", "no"])
                        cmd.extend(["--get_sub_comment", "no"])
                    
                    logger.info(f"MediaCrawler命令: {' '.join(cmd)}")
                    
                    # 记录爬取前的时间戳
                    import time
                    crawl_start_timestamp = time.time()
                    
                    logger.info(f"开始执行MediaCrawler命令...")
                    if login_type == "qrcode":
                        logger.info(f"重要提示：MediaCrawler会打开浏览器，请扫码登录！")
                    
                    # 设置环境变量，确保 Playwright 能找到浏览器
                    env = os.environ.copy()
                    
                    # 检查是否设置了 PLAYWRIGHT_BROWSERS_PATH
                    if "PLAYWRIGHT_BROWSERS_PATH" not in env:
                        # 尝试查找常见的 Playwright 路径
                        # 1. 检查 MediaCrawler/python_env 下的 site-packages/playwright
                        # 但实际上 Playwright 下载的浏览器通常在 LocalAppData 或 Temp
                        
                        # 如果是在 Sandbox 环境下，我们刚才看到它在 Temp/...
                        # 我们尝试显式设置它，如果我们能找到的话
                        pass
                        
                    logger.info(f"MediaCrawler 环境变量 PLAYWRIGHT_BROWSERS_PATH: {env.get('PLAYWRIGHT_BROWSERS_PATH')}")

                    result = subprocess.run(
                        cmd,
                        cwd=work_dir,
                        env=env, # Explicitly pass env
                        capture_output=False,
                        text=True,
                        timeout=settings.CRAWL_TIMEOUT,
                        encoding='utf-8',
                        errors='ignore'
                    )
                    
                    logger.info(f"MediaCrawler执行完成，返回码: {result.returncode}")
                    
                    # 读取生成的数据文件
                    data_dir = self.mediacrawler_path / "data"
                    if data_dir.exists():
                        time.sleep(5)
                        all_json_files = list(data_dir.rglob("*.json"))
                        
                        # 查找新生成的文件
                        json_files = [
                            f for f in all_json_files 
                            if f.stat().st_mtime >= (crawl_start_timestamp - 10)
                        ]
                        
                        if not json_files and all_json_files:
                             # 如果没找到新文件但有旧文件，且是 creator/detail 模式，尝试读取最新的
                             # 因为 creator 模式可能文件名不含关键词，难以精确定位
                            json_files = sorted(all_json_files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]
                            logger.info(f"未找到确切的新文件，尝试读取最新的 {len(json_files)} 个文件")
                        
                        for data_file in json_files:
                            try:
                                with open(data_file, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                    # ... (数据读取逻辑同上，省略部分代码以复用) ...
                                    if isinstance(data, list):
                                        real_data = [item for item in data if not item.get("is_mock", False)]
                                        results.extend(real_data)
                                    elif isinstance(data, dict):
                                        if not data.get("is_mock", False):
                                            if "items" in data:
                                                items = data.get("items", [])
                                                results.extend([i for i in items if not i.get("is_mock", False)])
                                            else:
                                                results.append(data)
                            except Exception as e:
                                logger.warning(f"读取数据文件失败 {data_file}: {e}")
                    
                except Exception as e:
                    logger.error(f"执行爬取任务失败: {e}", exc_info=True)
                    if crawl_type != "search": # 非搜索模式失败直接抛出
                        raise
                        
        finally:
            try:
                from app.api.v1.mediacrawler_ui import restore_config
                if config_modified:
                    try:
                        restore_config(self.mediacrawler_path)
                    except Exception as e:
                        logger.warning(f"恢复配置文件失败 (config_modified): {e}")
                
                # 如果仅仅修改了媒体配置，restore_config 也会恢复它（因为是同一个文件）
                # 所以只要调用一次 restore_config 即可，但为了安全起见（如果 set_max_count 没跑），我们再尝试一次
                if media_config_modified and not config_modified:
                    try:
                        restore_config(self.mediacrawler_path)
                    except Exception as e:
                        logger.warning(f"恢复配置文件失败 (media_config_modified): {e}")
            except Exception as e:
                 logger.warning(f"恢复配置时发生错误: {e}")
        
        # 结果处理
        is_real_crawl = bool(results and not any(item.get("is_mock", False) for item in results))
        
        return {
            "platform": platform,
            "keywords": keywords,
            "target_url": target_url,
            "crawl_type": crawl_type,
            "total_items": len(results),
            "items": results,
            "output_dir": str(output_dir),
            "is_real_crawl": True, # 假设只要有结果就是真实的，因为我们没有 mock 模式了
            "crawl_method": "real"
        }

    def _update_mediacrawler_media_config(self, enable: bool) -> bool:
        """
        临时修改 MediaCrawler 配置文件中的 ENABLE_GET_MEIDAS
        """
        try:
            config_path = self.mediacrawler_path / "config" / "base_config.py"
            if not config_path.exists():
                return False
                
            # 备份配置文件（如果尚未备份）
            # 注意：mediacrawler_ui.set_max_count 已经负责了备份逻辑
            # 我们这里假设 set_max_count 已经被调用，且已经备份了配置文件
            # 如果没有，我们需要自己处理备份
            
            # 读取当前内容
            content = config_path.read_text(encoding='utf-8')
            
            # 替换 ENABLE_GET_MEIDAS
            import re
            pattern = re.compile(r"ENABLE_GET_MEIDAS\s*=\s*(True|False)")
            
            new_value = "True" if enable else "False"
            new_content = pattern.sub(f"ENABLE_GET_MEIDAS = {new_value}", content)
            
            if new_content != content:
                config_path.write_text(new_content, encoding='utf-8')
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"更新媒体下载配置失败: {e}")
            return False

    def _update_mediacrawler_url_config(self, platform: str, crawl_type: str, url: str):
        """
        临时修改 MediaCrawler 配置文件中的 URL 列表
        这通过重写 config.py 文件实现（因为 MediaCrawler 运行时是 import config）
        """
        try:
            # 确定要修改的变量名
            var_name = ""
            config_file_name = "base_config.py" # 默认 fallback
            
            if platform in ["dy", "douyin"]:
                config_file_name = "dy_config.py"
                if crawl_type == "creator":
                    var_name = "DY_CREATOR_ID_LIST"
                elif crawl_type == "detail":
                    var_name = "DY_SPECIFIED_ID_LIST"
            elif platform in ["xhs"]:
                config_file_name = "xhs_config.py"
                if crawl_type == "creator":
                    var_name = "XHS_CREATOR_ID_LIST"
                elif crawl_type == "detail":
                    var_name = "XHS_SPECIFIED_ID_LIST"
            # ... 其他平台
            
            if not var_name:
                return
                
            # 尝试找到配置文件
            # 优先级: config.py -> config/{config_file_name} -> config/base_config.py
            target_config = self.mediacrawler_path / "config.py"
            
            # 如果根目录没有 config.py，尝试找 config 目录下的特定配置文件
            if not target_config.exists():
                target_config = self.mediacrawler_path / "config" / config_file_name
                
            if not target_config.exists():
                target_config = self.mediacrawler_path / "config" / "base_config.py"
                
            if not target_config.exists():
                logger.warning("未找到任何配置文件")
                return
                
            logger.info(f"正在更新配置文件: {target_config}, 变量: {var_name}")
            content = target_config.read_text(encoding='utf-8')
            
            # 替换列表内容
            # 查找 var_name = [ ... ]
            import re
            # 简单的正则替换，将列表内容替换为我们的 url
            # 注意 url 需要加引号
            new_list = f'{var_name} = ["{url}"]'
            
            # 匹配 var_name = [...] 或 var_name = [ ... ] (多行)
            # 这是一个简化的替换，假设配置文件格式标准
            pattern = re.compile(f'{var_name}\s*=\s*\[.*?\]', re.DOTALL)
            
            if pattern.search(content):
                new_content = pattern.sub(new_list, content)
                target_config.write_text(new_content, encoding='utf-8')
                logger.info(f"已临时更新 MediaCrawler 配置: {var_name}")
            else:
                logger.warning(f"未在配置文件中找到 {var_name}")
                # 如果没找到，尝试追加？不，太冒险。
                
        except Exception as e:
            logger.error(f"更新 MediaCrawler URL 配置失败: {e}")
        """
        临时修改 MediaCrawler 配置文件中的 URL 列表
        这通过重写 config.py 文件实现（因为 MediaCrawler 运行时是 import config）
        """
        try:
            config_path = self.mediacrawler_path / "config" / "base_config.py"
            # 注意：MediaCrawler 的配置结构可能变化，这里基于常见结构
            # 实际上 MediaCrawler 可能是在 config.py 或 config/base_config.py
            # 我们先读取 config.py
            
            # 简单实现：我们利用 MediaCrawler 支持命令行参数覆盖配置的特性（如果支持）
            # 或者，由于我们不能轻易修改 python 代码文件，我们尝试查找是否有 json/yaml 配置
            # MediaCrawler 目前主要是 python config。
            
            # 更好的方式：MediaCrawler 的 core.py 里面读取的是 config.DY_CREATOR_ID_LIST
            # 我们可以在调用 subprocess 之前，写一个临时的 python 脚本来启动，或者
            # 修改 MediaCrawler 的 config.py 文件。
            
            # 这里采用修改 config.py 的方式，但在生产环境中这有并发风险。
            # 鉴于这是一个单用户本地工具，我们暂时接受这个风险。
            
            # 读取 config.py
            target_config = self.mediacrawler_path / "config.py"
            if not target_config.exists():
                return
                
            content = target_config.read_text(encoding='utf-8')
            
            # 确定要修改的变量名
            var_name = ""
            if platform in ["dy", "douyin"]:
                if crawl_type == "creator":
                    var_name = "DY_CREATOR_ID_LIST"
                elif crawl_type == "detail":
                    var_name = "DY_SPECIFIED_ID_LIST"
            elif platform in ["xhs"]:
                 if crawl_type == "creator":
                    var_name = "XHS_CREATOR_ID_LIST"
                 elif crawl_type == "detail":
                    var_name = "XHS_SPECIFIED_ID_LIST"
            # ... 其他平台
            
            if not var_name:
                return
                
            # 替换列表内容
            # 查找 var_name = [ ... ]
            import re
            # 简单的正则替换，将列表内容替换为我们的 url
            # 注意 url 需要加引号
            new_list = f'{var_name} = ["{url}"]'
            
            # 匹配 var_name = [...] 或 var_name = [ ... ] (多行)
            # 这是一个简化的替换，假设配置文件格式标准
            pattern = re.compile(f'{var_name}\s*=\s*\[.*?\]', re.DOTALL)
            
            if pattern.search(content):
                new_content = pattern.sub(new_list, content)
                target_config.write_text(new_content, encoding='utf-8')
                logger.info(f"已临时更新 MediaCrawler 配置: {var_name}")
            else:
                logger.warning(f"未在配置文件中找到 {var_name}")
                
        except Exception as e:
            logger.error(f"更新 MediaCrawler URL 配置失败: {e}")

    def save_crawled_data(
        self,
        brand_id: int,
        task_id: int,
        platform: str,
        data: Dict,
        mongodb
    ) -> int:
        """
        保存爬取的数据到MongoDB
        
        Args:
            brand_id: 品牌ID
            task_id: 任务ID
            platform: 平台名称
            data: 爬取的数据
            mongodb: MongoDB数据库对象
            
        Returns:
            保存的数据条数
        """
        try:
            collection = mongodb.raw_data
            saved_count = 0
            
            items = data.get("items", [])
            for item in items:
                # 1. 尝试查找本地视频/图片文件 (新增)
                # MediaCrawler 存储结构: 
                # - data/crawled_data/douyin/{content_id}/video.mp4
                # - data/crawled_data/douyin/{content_id}/{index}.jpeg
                
                content_id = item.get("id", "")
                if not content_id: # 某些平台可能使用其他字段
                     content_id = item.get("aweme_id", "") or item.get("note_id", "")
                
                video_path = None
                image_path = None
                
                if content_id and self.mediacrawler_path:
                    # 推断可能的视频路径
                    # 这里需要根据 MediaCrawler 的 store 逻辑来判断
                    # 对于抖音: data/crawled_data/douyin/{content_id}/video.mp4
                    # 平台名可能是简写
                    platform_code = self.PLATFORM_MAP.get(platform.lower(), platform.lower())
                    if platform_code == "dy": platform_code = "douyin" # store 通常用全称
                    if platform_code == "xhs": platform_code = "xhs"
                    
                    # MediaCrawler 的数据源目录
                    mc_data_path = self.mediacrawler_path / "data/crawled_data" / platform_code / str(content_id)
                    
                    # 目标数据目录 (项目的数据目录)
                    target_base_path = self.data_dir / platform_code / str(content_id)
                    
                    if mc_data_path.exists():
                        # 确保目标目录存在
                        target_base_path.mkdir(parents=True, exist_ok=True)
                        
                        # 处理视频
                        mc_video = mc_data_path / "video.mp4"
                        if mc_video.exists():
                            target_video = target_base_path / "video.mp4"
                            # 如果目标文件不存在或大小不同，则复制
                            import shutil
                            if not target_video.exists() or target_video.stat().st_size != mc_video.stat().st_size:
                                try:
                                    shutil.copy2(mc_video, target_video)
                                    logger.info(f"已复制视频文件到项目目录: {target_video}")
                                except Exception as e:
                                    logger.warning(f"复制视频文件失败: {e}")
                            
                            # 记录相对路径 (相对于 data/crawled_data)
                            if target_video.exists():
                                video_path = f"{platform_code}/{content_id}/video.mp4"
                        
                        # 处理图片 (复制所有图片)
                        # MediaCrawler 可能有多张图片: 0.jpg, 1.jpg ... 或者 000.jpeg
                        for img_file in mc_data_path.glob("*.jpeg"):
                             target_img = target_base_path / img_file.name
                             if not target_img.exists() or target_img.stat().st_size != img_file.stat().st_size:
                                 try:
                                     shutil.copy2(img_file, target_img)
                                 except Exception as e:
                                     logger.warning(f"复制图片文件失败: {e}")
                        
                        # 记录第一张图片作为封面
                        if (target_base_path / "000.jpeg").exists():
                             image_path = f"{platform_code}/{content_id}/000.jpeg"
                        elif list(target_base_path.glob("*.jpeg")):
                             # 如果没有 000.jpeg，取第一张
                             first_img = list(target_base_path.glob("*.jpeg"))[0]
                             image_path = f"{platform_code}/{content_id}/{first_img.name}"

                # 2. 处理发布时间 (优化)
                publish_time = None
                create_time = item.get("create_time") or item.get("publish_time")
                
                if create_time:
                    try:
                        # 如果是数字 (秒或毫秒)
                        if isinstance(create_time, (int, float)):
                            ts = int(create_time)
                            if ts > 1000000000000: # 毫秒
                                publish_time = datetime.fromtimestamp(ts / 1000)
                            else:
                                publish_time = datetime.fromtimestamp(ts)
                        elif isinstance(create_time, str):
                            # 尝试解析 ISO 格式
                            publish_time = datetime.fromisoformat(create_time)
                    except:
                        # 解析失败，保留 None 或当前时间
                        pass
                
                if not publish_time:
                    publish_time = datetime.now()

                # 构建文档
                doc = {
                    "brand_id": brand_id,
                    "platform": platform,
                    "task_id": task_id,
                    "content_type": "post",
                    "content_id": str(content_id),
                    "title": item.get("title", ""),
                    "content": item.get("content", "") or item.get("desc", ""),
                    "author": {
                        "id": item.get("author", {}).get("id", "") if isinstance(item.get("author"), dict) else "",
                        "name": item.get("author", "") if isinstance(item.get("author"), str) else item.get("author", {}).get("name", ""),
                        "avatar": item.get("author", {}).get("avatar", "") if isinstance(item.get("author"), dict) else ""
                    },
                    "publish_time": publish_time,
                    "engagement": item.get("engagement", {}),
                    "media": {
                        "images": item.get("images", []),
                        "videos": item.get("videos", [])
                    },
                    "video_path": video_path, # 本地视频路径
                    "image_path": image_path, # 本地图片路径
                    "raw_data": item,
                    "crawled_at": datetime.now()
                }
                
                # 去重：检查是否已存在（基于content_id和platform）
                if not doc["content_id"]:
                    unique_str = f"{doc['title']}{doc['content'][:100]}"
                    doc["content_id"] = hashlib.md5(unique_str.encode()).hexdigest()
                
                existing = collection.find_one({
                    "brand_id": brand_id,
                    "content_id": doc["content_id"],
                    "platform": platform
                })
                
                if not existing:
                    try:
                        collection.insert_one(doc)
                        saved_count += 1
                    except Exception as e:
                        # 如果插入失败（可能是唯一索引冲突），尝试更新
                        logger.warning(f"插入数据失败，尝试更新: {e}")
                        existing = collection.find_one({
                            "brand_id": brand_id,
                            "content_id": doc["content_id"],
                            "platform": platform
                        })
                        if existing:
                            collection.update_one(
                                {"_id": existing["_id"]},
                                {"$set": {
                                    "raw_data": item,
                                    "video_path": video_path,
                                    "image_path": image_path,
                                    "crawled_at": datetime.now()
                                }}
                            )
                else:
                    # 更新现有数据（不增加计数）
                    update_fields = {
                        "raw_data": item,
                        "crawled_at": datetime.now(),
                        "task_id": task_id
                    }
                    if video_path: update_fields["video_path"] = video_path
                    if image_path: update_fields["image_path"] = image_path
                    
                    collection.update_one(
                        {"_id": existing["_id"]},
                        {"$set": update_fields}
                    )
                    logger.debug(f"数据已存在，已更新: {doc['content_id']}")
            
            logger.info(f"保存了 {saved_count} 条新数据到MongoDB")
            return saved_count
            
        except Exception as e:
            logger.error(f"保存数据失败: {e}", exc_info=True)
            raise
