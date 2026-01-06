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
        include_comments: bool = True,
        output_dir: Optional[Path] = None
    ) -> Dict:
        """
        爬取指定平台的数据
        
        Args:
            platform: 平台名称 (xhs, douyin, weibo, zhihu等)
            keywords: 关键词列表
            max_items: 最大采集数量
            include_comments: 是否包含评论
            output_dir: 输出目录
            
        Returns:
            爬取结果字典
        """
        try:
            # 转换平台名称
            platform_code = self.PLATFORM_MAP.get(platform.lower(), platform.lower())
            
            if not output_dir:
                output_dir = self.data_dir / platform / datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"开始爬取平台: {platform}, 关键词: {keywords}, 最大数量: {max_items}")
            
            # 检查MediaCrawler是否可用
            if not self.mediacrawler_path or not self.mediacrawler_path.exists():
                raise Exception(f"MediaCrawler目录不存在: {self.mediacrawler_path}")
            
            main_py = self.mediacrawler_path / "main.py"
            if not main_py.exists():
                raise Exception(f"MediaCrawler的main.py不存在: {main_py}")
            
            # 使用MediaCrawler进行真实爬取
            logger.info(f"使用MediaCrawler进行真实爬取: {self.mediacrawler_path}")
            result = self._crawl_with_mediacrawler(
                platform_code, keywords, max_items, include_comments, output_dir
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
        output_dir: Path
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
        try:
            from app.api.v1.mediacrawler_ui import set_max_count, restore_config
            config_modified = set_max_count(self.mediacrawler_path, max_items)
            if config_modified:
                logger.info(f"已设置最大爬取数量: {max_items}")
        except Exception as e:
            logger.warning(f"设置最大爬取数量失败: {e}")
        
        try:
            for keyword in keywords:
                try:
                    # 构建MediaCrawler命令（与Web界面保持一致）
                    # 根据MediaCrawler的实际参数格式构建命令
                    # 参考: https://github.com/NanmiCoder/MediaCrawler
                    all_keywords = ",".join(keywords)  # 合并所有关键词，用逗号分隔
                    
                    # 检查登录状态，如果已登录则使用cookie模式，避免每次都需要扫码
                    login_type = "qrcode"  # 默认使用二维码登录
                    if self.login_checker:
                        # 将MediaCrawler平台代码转换为内部平台代码
                        internal_platform = platform.lower()  # 使用原始平台代码
                        if self.login_checker.check_login_status(internal_platform):
                            login_type = "cookie"  # 已登录，使用cookie模式
                            logger.info(f"[{platform}] 检测到已保存的登录状态，使用cookie模式，无需扫码")
                        else:
                            logger.info(f"[{platform}] 未检测到登录状态，使用二维码登录模式")
                    
                    cmd = [
                        python_cmd,
                        str(main_py),
                        "--platform", mediacrawler_platform,  # 使用MediaCrawler的平台代码
                        "--lt", login_type,  # 登录类型：如果已登录则使用cookie，否则使用qrcode
                        "--type", "search",  # 搜索类型：搜索模式
                        "--keywords", all_keywords,  # 关键词（支持多个，逗号分隔）
                        "--save_data_option", "json",  # 保存为JSON格式
                    ]
                    
                    # 设置是否爬取评论（与Web界面保持一致）
                    if include_comments:
                        cmd.extend(["--get_comment", "yes"])
                        cmd.extend(["--get_sub_comment", "no"])  # 默认不获取子评论
                    else:
                        cmd.extend(["--get_comment", "no"])
                        cmd.extend(["--get_sub_comment", "no"])
                    
                    logger.info(f"MediaCrawler命令: {' '.join(cmd)}")
                    
                    # 设置最大爬取数量（如果MediaCrawler支持）
                    # 注意：MediaCrawler使用CRAWLER_MAX_NOTES_COUNT配置，可能需要修改配置文件
                    # 这里先通过命令行尝试，如果不支持会在配置文件中设置
                    
                    # 设置输出目录（如果MediaCrawler支持）
                    # 注意：MediaCrawler可能使用配置文件，这里先尝试
                    
                    logger.info(f"执行MediaCrawler命令: {' '.join(cmd)}")
                    logger.info(f"工作目录: {work_dir}")
                    
                    # 记录爬取前的时间戳（在命令执行前）
                    import time
                    crawl_start_timestamp = time.time()
                    
                    # 执行爬虫命令
                    # 注意：MediaCrawler需要打开浏览器进行登录，不能使用capture_output=True
                    # 否则浏览器窗口会被隐藏，无法扫码登录
                    logger.info(f"开始执行MediaCrawler命令...")
                    if login_type == "qrcode":
                        logger.info(f"重要提示：MediaCrawler会打开浏览器，请扫码登录！")
                        logger.info(f"如果浏览器未打开，请检查MediaCrawler配置中的HEADLESS设置")
                    else:
                        logger.info(f"使用已保存的登录状态，无需扫码")
                    
                    result = subprocess.run(
                        cmd,
                        cwd=work_dir,  # 设置工作目录
                        capture_output=False,  # 不使用capture_output，让浏览器窗口显示
                        text=True,
                        timeout=settings.CRAWL_TIMEOUT,  # 使用配置的超时时间
                        encoding='utf-8',
                        errors='ignore'
                    )
                    
                    logger.info(f"MediaCrawler执行完成，返回码: {result.returncode}")
                    if result.stdout:
                        logger.info(f"标准输出: {result.stdout[:1000]}")
                    if result.stderr:
                        logger.warning(f"错误输出: {result.stderr[:1000]}")
                    
                    # 无论返回码是什么，都尝试读取数据（因为MediaCrawler可能已经保存了数据）
                    # MediaCrawler通常将数据保存到data目录
                    data_dir = self.mediacrawler_path / "data"
                    if data_dir.exists():
                        # 等待一下，确保文件已写入（MediaCrawler可能需要时间保存数据）
                        time.sleep(5)  # 增加等待时间
                        
                        # 查找最新的JSON文件（爬取后生成的，时间戳在爬取开始之后）
                        # MediaCrawler可能将数据保存到子目录中，如 data/xhs/json/
                        all_json_files = list(data_dir.rglob("*.json"))  # 使用rglob递归查找所有子目录
                        
                        # 查找在爬取开始后生成的文件（允许10秒误差，因为文件系统时间可能有延迟）
                        json_files = [
                            f for f in all_json_files 
                            if f.stat().st_mtime >= (crawl_start_timestamp - 10)  # 允许10秒误差
                        ]
                        
                        if not json_files:
                            # 如果没找到新文件，可能是：
                            # 1. MediaCrawler执行失败
                            # 2. MediaCrawler需要登录但未登录
                            # 3. 文件保存延迟
                            logger.warning("未找到爬取后新生成的文件")
                            logger.warning("可能原因：1) MediaCrawler执行失败 2) 需要登录 3) 文件保存延迟")
                            
                            # 尝试读取最新的几个文件（可能是MediaCrawler保存延迟）
                            if all_json_files:
                                json_files = sorted(all_json_files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]
                                logger.info(f"尝试读取最新的 {len(json_files)} 个文件（可能不是本次爬取的数据）")
                            else:
                                logger.error("MediaCrawler数据目录为空，可能MediaCrawler未正确执行")
                        else:
                            logger.info(f"找到 {len(json_files)} 个新生成的数据文件")
                        
                        # 读取数据文件
                        for data_file in json_files:
                            try:
                                logger.info(f"读取数据文件: {data_file.name} (修改时间: {datetime.fromtimestamp(data_file.stat().st_mtime)})")
                                with open(data_file, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                    
                                    # 处理列表格式的数据
                                    if isinstance(data, list):
                                        # 过滤掉模拟数据（如果有is_mock标记）
                                        real_data = [item for item in data if not item.get("is_mock", False)]
                                        if real_data:
                                            results.extend(real_data)
                                            logger.info(f"从 {data_file.name} 读取 {len(real_data)} 条真实数据")
                                        else:
                                            logger.warning(f"文件 {data_file.name} 中的数据被标记为模拟数据或为空")
                                    # 处理字典格式的数据
                                    elif isinstance(data, dict):
                                        if not data.get("is_mock", False):
                                            # 如果是单个数据项，转换为列表
                                            if "items" in data:
                                                items = data.get("items", [])
                                                real_items = [item for item in items if not item.get("is_mock", False)]
                                                results.extend(real_items)
                                                logger.info(f"从 {data_file.name} 读取 {len(real_items)} 条真实数据")
                                            else:
                                                results.append(data)
                                                logger.info(f"从 {data_file.name} 读取 1 条真实数据")
                                        else:
                                            logger.warning(f"文件 {data_file.name} 中的数据被标记为模拟数据")
                            except json.JSONDecodeError as e:
                                logger.error(f"JSON解析失败 {data_file}: {e}")
                            except Exception as e:
                                logger.warning(f"读取数据文件失败 {data_file}: {e}")
                        
                        if not results:
                            logger.warning("未从MediaCrawler数据文件中读取到数据，可能原因：")
                            logger.warning("1. MediaCrawler未成功爬取数据")
                            logger.warning("2. 数据文件格式不匹配")
                            logger.warning("3. 数据文件生成延迟（可以增加等待时间）")
                    else:
                        logger.warning(f"MediaCrawler数据目录不存在: {data_dir}")
                        logger.warning("MediaCrawler可能未正确配置数据保存路径")
                    
                    # 如果MediaCrawler执行失败且没有读取到数据，直接抛出异常
                    if result.returncode != 0 and not results:
                        error_msg = f"MediaCrawler执行失败 (返回码: {result.returncode})"
                        logger.error(error_msg)
                        if result.stderr:
                            logger.error(f"错误输出: {result.stderr[:500]}")
                        raise Exception(f"{error_msg}: {result.stderr[:200] if result.stderr else '无错误信息'}")
                        
                except subprocess.TimeoutExpired:
                    error_msg = f"MediaCrawler超时: {keyword}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                except Exception as e:
                    logger.error(f"爬取关键词 {keyword} 失败: {e}", exc_info=True)
                    raise  # 直接抛出异常，不降级到模拟数据
        finally:
            # 恢复配置文件（如果修改过，与Web界面保持一致）
            if config_modified:
                try:
                    from app.api.v1.mediacrawler_ui import restore_config
                    restore_config(self.mediacrawler_path)
                    logger.info("已恢复MediaCrawler配置文件")
                except Exception as e:
                    logger.warning(f"恢复配置文件失败: {e}")
        
        # 如果没有获取到数据，抛出异常
        if not results:
            raise Exception("MediaCrawler执行完成但未获取到任何数据")
        
        # 判断是否为真实爬取：有结果且没有is_mock标记
        is_real_crawl = bool(results and not any(item.get("is_mock", False) for item in results))
        
        if not is_real_crawl:
            raise Exception("获取到的数据包含模拟数据标记，爬取失败")
        
        return {
            "platform": platform,
            "keywords": keywords,
            "total_items": len(results),
            "items": results,
            "output_dir": str(output_dir),
            "is_real_crawl": True,
            "crawl_method": "real"
        }
    
    def _crawl_mock_data(
        self,
        platform: str,
        keywords: List[str],
        max_items: int
    ) -> Dict:
        """生成模拟数据（用于开发测试）"""
        import random
        
        mock_items = []
        for i in range(min(max_items, 10)):  # 最多生成10条模拟数据
            mock_items.append({
                "id": f"{platform}_{i+1}",
                "platform": platform,
                "keyword": keywords[0] if keywords else "",
                "title": f"关于{keywords[0] if keywords else '品牌'}的测试内容 {i+1}",
                "content": f"这是从{platform}平台爬取的关于{keywords[0] if keywords else '品牌'}的测试内容。",
                "author": f"用户_{i+1}",
                "publish_time": (datetime.now()).isoformat(),
                "engagement": {
                    "likes": random.randint(10, 1000),
                    "comments": random.randint(5, 500),
                    "shares": random.randint(0, 100),
                    "views": random.randint(100, 10000)
                },
                "url": f"https://{platform}.com/post/{i+1}",
                "crawled_at": datetime.now().isoformat()
            })
        
        logger.info(f"生成 {len(mock_items)} 条模拟数据")
        
        return {
            "platform": platform,
            "keywords": keywords,
            "total_items": len(mock_items),
            "items": mock_items,
            "is_mock": True
        }
    
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
                # 构建文档
                doc = {
                    "brand_id": brand_id,
                    "platform": platform,
                    "task_id": task_id,
                    "content_type": "post",  # 或从数据中判断
                    "content_id": item.get("id", ""),
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "author": {
                        "id": item.get("author", {}).get("id", "") if isinstance(item.get("author"), dict) else "",
                        "name": item.get("author", "") if isinstance(item.get("author"), str) else item.get("author", {}).get("name", ""),
                        "avatar": item.get("author", {}).get("avatar", "") if isinstance(item.get("author"), dict) else ""
                    },
                    "publish_time": datetime.fromisoformat(item.get("publish_time", datetime.now().isoformat())) if isinstance(item.get("publish_time"), str) else item.get("publish_time"),
                    "engagement": item.get("engagement", {}),
                    "media": {
                        "images": item.get("images", []),
                        "videos": item.get("videos", [])
                    },
                    "raw_data": item,
                    "crawled_at": datetime.now()
                }
                
                # 去重：检查是否已存在（基于content_id和platform）
                # 如果content_id为空，使用URL或title+content的hash作为唯一标识
                if not doc["content_id"]:
                    # 使用title+content的前100字符生成唯一标识
                    unique_str = f"{doc['title']}{doc['content'][:100]}"
                    doc["content_id"] = hashlib.md5(unique_str.encode()).hexdigest()
                
                existing = collection.find_one({
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
                            "content_id": doc["content_id"],
                            "platform": platform
                        })
                        if existing:
                            collection.update_one(
                                {"_id": existing["_id"]},
                                {"$set": {
                                    "raw_data": item,
                                    "crawled_at": datetime.now()
                                }}
                            )
                else:
                    # 更新现有数据（不增加计数）
                    collection.update_one(
                        {"_id": existing["_id"]},
                        {"$set": {
                            "raw_data": item,
                            "crawled_at": datetime.now(),
                            "task_id": task_id  # 更新任务ID
                        }}
                    )
                    logger.debug(f"数据已存在，已更新: {doc['content_id']}")
            
            logger.info(f"保存了 {saved_count} 条新数据到MongoDB")
            return saved_count
            
        except Exception as e:
            logger.error(f"保存数据失败: {e}", exc_info=True)
            raise

