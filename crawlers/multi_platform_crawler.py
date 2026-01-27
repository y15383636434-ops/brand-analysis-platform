"""
多平台爬虫
支持同时爬取多个平台
"""
from typing import Dict, List, Optional
from loguru import logger
import time
import requests
import json

from .base_crawler import BaseCrawler
from . import (
    XHSCrawler,
    DouyinCrawler,
    WeiboCrawler,
    ZhihuCrawler,
    BilibiliCrawler,
    KuaishouCrawler
)

# 平台映射
PLATFORM_CRAWLERS = {
    "xhs": XHSCrawler,
    "douyin": DouyinCrawler,
    "weibo": WeiboCrawler,
    "zhihu": ZhihuCrawler,
    "bilibili": BilibiliCrawler,
    "kuaishou": KuaishouCrawler,
}

PLATFORM_NAMES = {
    "xhs": "小红书",
    "douyin": "抖音",
    "weibo": "微博",
    "zhihu": "知乎",
    "bilibili": "B站",
    "kuaishou": "快手",
}


class MultiPlatformCrawler:
    """多平台爬虫类"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1"
    
    def check_service(self) -> bool:
        """检查服务是否运行"""
        try:
            # 尝试多个端点，提高成功率
            endpoints = [
                "http://localhost:8000/health",
                "http://localhost:8000/docs",
                "http://127.0.0.1:8000/health"
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(endpoint, timeout=3)
                    if response.status_code in [200, 404]:  # 404也算服务在运行
                        logger.debug(f"服务检查成功: {endpoint}")
                        return True
                except requests.exceptions.RequestException:
                    continue
            
            # 如果所有端点都失败，尝试直接检查API
            try:
                response = requests.get(f"{self.base_url}/brands?page_size=1", timeout=3)
                if response.status_code in [200, 401, 403]:  # 即使需要认证也算服务在运行
                    logger.debug("服务检查成功: API端点")
                    return True
            except:
                pass
            
            logger.warning("服务检查失败: 所有端点都无法访问")
            return False
        except Exception as e:
            logger.error(f"服务检查异常: {e}")
            # 如果检查失败，假设服务在运行（因为可能只是网络问题）
            # 让后续的API调用来验证
            return True
    
    def crawl_multiple_platforms(
        self,
        platforms: List[str],
        brand_name: str,
        keywords: List[str],
        max_items: int = 10,
        include_comments: bool = True,
        download_media: bool = True,
        parallel: bool = False
    ) -> Dict:
        """
        爬取多个平台
        
        Args:
            platforms: 平台代码列表，如 ["xhs", "douyin"]
            brand_name: 品牌名称
            keywords: 关键词列表
            max_items: 最大爬取数量
            include_comments: 是否包含评论
            download_media: 是否下载媒体文件
            parallel: 是否并行执行（暂不支持，使用串行）
            
        Returns:
            爬取结果字典
        """
        print("="*60)
        print("多平台爬虫")
        print("="*60)
        print(f"品牌名称: {brand_name}")
        print(f"关键词: {', '.join(keywords)}")
        print(f"平台: {', '.join([PLATFORM_NAMES.get(p, p) for p in platforms])}")
        print(f"最大数量: {max_items}")
        print(f"包含评论: {include_comments}")
        print(f"下载媒体: {download_media}")
        print()
        
        # 检查服务（如果检查失败，继续尝试，让实际API调用来验证）
        service_ok = self.check_service()
        if service_ok:
            print("[OK] 服务运行正常\n")
        else:
            print("[!] 服务检查失败，但将继续尝试...\n")
        
        # 验证平台
        invalid_platforms = [p for p in platforms if p not in PLATFORM_CRAWLERS]
        if invalid_platforms:
            return {
                "success": False,
                "error": f"无效的平台: {', '.join(invalid_platforms)}"
            }
        
        # 创建品牌（所有平台共享一个品牌）
        print("1. 创建品牌...")
        brand_data = {
            "name": brand_name,
            "description": f"{brand_name}品牌分析",
            "keywords": keywords,
            "platforms": platforms
        }
        
        try:
            response = requests.post(f"{self.base_url}/brands", json=brand_data, timeout=10)
            if response.status_code in [200, 201]:
                result = response.json()
                # 处理不同的响应格式
                brand_id = None
                
                # 格式1: 直接返回BrandResponse对象 {"id": 1, "name": "...", ...}
                if "id" in result:
                    brand_id = result["id"]
                # 格式2: 包装在data中 {"data": {"id": 1, ...}}
                elif "data" in result and isinstance(result["data"], dict) and "id" in result["data"]:
                    brand_id = result["data"]["id"]
                # 格式3: 可能是其他格式
                else:
                    # 尝试从响应中提取ID
                    logger.warning(f"品牌创建响应格式异常: {result}")
                    # 如果响应中有任何数字ID，尝试使用
                    if isinstance(result, dict):
                        for key in ["id", "brand_id", "data"]:
                            if key in result:
                                value = result[key]
                                if isinstance(value, dict) and "id" in value:
                                    brand_id = value["id"]
                                    break
                                elif isinstance(value, int):
                                    brand_id = value
                                    break
                
                if brand_id:
                    print(f"[OK] 品牌创建成功，ID: {brand_id}\n")
                else:
                    # 最后尝试：打印完整响应用于调试
                    logger.error(f"无法从响应中获取品牌ID。完整响应: {json.dumps(result, ensure_ascii=False)}")
                    return {
                        "success": False,
                        "error": f"创建品牌失败：无法从响应中获取品牌ID。请查看日志了解详情。"
                    }
            else:
                error_msg = f"创建品牌失败: HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_msg += f" - {error_data['detail']}"
                    elif "message" in error_data:
                        error_msg += f" - {error_data['message']}"
                except:
                    error_msg += f" - {response.text[:100]}"
                
                return {
                    "success": False,
                    "error": error_msg
                }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "无法连接到服务。请确保服务正在运行: python 一键启动.py"
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "创建品牌请求超时（10秒）。请检查服务状态或稍后重试。"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"创建品牌失败: {str(e)}。请确保服务正在运行。"
            }
        
        # 为每个平台创建爬取任务
        print("2. 创建爬取任务...")
        task_results = []
        
        for platform in platforms:
            platform_name = PLATFORM_NAMES.get(platform, platform)
            print(f"\n   平台: {platform_name} ({platform})")
            
            task_data = {
                "platforms": [platform],
                "keywords": keywords,
                "max_items": max_items,
                "include_comments": include_comments,
                "download_media": download_media
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/brands/{brand_id}/crawl",
                    json=task_data,
                    timeout=30  # 创建任务可能需要更长时间
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "data" in result and "task_ids" in result["data"]:
                        task_ids = result["data"]["task_ids"]
                        if task_ids:
                            task_id = task_ids[0]
                            print(f"   [OK] 任务创建成功，任务ID: {task_id}")
                            task_results.append({
                                "platform": platform,
                                "platform_name": platform_name,
                                "task_id": task_id,
                                "status": "created"
                            })
                        else:
                            print(f"   [X] 任务ID列表为空")
                            task_results.append({
                                "platform": platform,
                                "platform_name": platform_name,
                                "status": "failed",
                                "error": "任务ID列表为空"
                            })
                    else:
                        print(f"   [X] 响应格式异常")
                        task_results.append({
                            "platform": platform,
                            "platform_name": platform_name,
                            "status": "failed",
                            "error": "响应格式异常"
                        })
                else:
                    error_msg = f"HTTP {response.status_code}"
                    try:
                        error_data = response.json()
                        if "detail" in error_data:
                            error_msg = error_data["detail"]
                        elif "message" in error_data:
                            error_msg = error_data["message"]
                    except:
                        pass
                    print(f"   [X] 创建任务失败: {error_msg}")
                    task_results.append({
                        "platform": platform,
                        "platform_name": platform_name,
                        "status": "failed",
                        "error": error_msg
                    })
            except requests.exceptions.Timeout:
                print(f"   [X] 创建任务超时（30秒）")
                task_results.append({
                    "platform": platform,
                    "platform_name": platform_name,
                    "status": "failed",
                    "error": "请求超时（30秒），任务可能仍在后台创建中"
                })
            except requests.exceptions.ConnectionError:
                print(f"   [X] 无法连接到服务")
                task_results.append({
                    "platform": platform,
                    "platform_name": platform_name,
                    "status": "failed",
                    "error": "无法连接到服务"
                })
            except Exception as e:
                print(f"   [X] 创建任务失败: {e}")
                task_results.append({
                    "platform": platform,
                    "platform_name": platform_name,
                    "status": "failed",
                    "error": str(e)
                })
        
        print("\n" + "="*60)
        successful_count = len([t for t in task_results if t.get("task_id")])
        failed_count = len([t for t in task_results if not t.get("task_id")])
        
        if successful_count > 0:
            print("任务已启动！")
            print("="*60)
            print(f"\n成功创建: {successful_count} 个任务")
            if failed_count > 0:
                print(f"创建失败: {failed_count} 个任务")
            print("\n提示:")
            print("1. 所有任务在后台执行，请查看Celery Worker窗口")
            print("2. 首次使用可能需要扫码登录（某些平台）")
            print("3. 等待1-3分钟后查看结果")
            print()
            
            # 显示任务信息
            print("任务列表:")
            for task in task_results:
                if task.get("task_id"):
                    print(f"  ✅ {task['platform_name']}: 任务ID {task['task_id']}")
                else:
                    print(f"  ❌ {task['platform_name']}: {task.get('error', '创建失败')}")
            
            print("\n" + "="*60)
            print("查看结果")
            print("="*60)
            print(f"数据统计: GET {self.base_url}/brands/{brand_id}/data/stats")
            print(f"数据列表: GET {self.base_url}/brands/{brand_id}/data")
            print(f"API文档: http://localhost:8000/docs")
            
            return {
                "success": True,
                "brand_id": brand_id,
                "platforms": platforms,
                "tasks": task_results,
                "total_tasks": len(task_results),
                "successful_tasks": successful_count,
                "failed_tasks": failed_count
            }
        else:
            # 所有任务都失败了
            error_messages = [t.get("error", "未知错误") for t in task_results if not t.get("task_id")]
            return {
                "success": False,
                "error": f"所有任务创建失败: {', '.join(set(error_messages))}",
                "brand_id": brand_id,
                "tasks": task_results
            }

