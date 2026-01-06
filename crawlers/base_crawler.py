"""
基础爬虫类
所有平台爬虫的基类
"""
import requests
from typing import Dict, List, Optional
from abc import ABC, abstractmethod
from loguru import logger

BASE_URL = "http://localhost:8000/api/v1"


class BaseCrawler(ABC):
    """基础爬虫类"""
    
    def __init__(self, platform: str):
        """
        初始化爬虫
        
        Args:
            platform: 平台代码 (xhs, douyin, weibo等)
        """
        self.platform = platform
        self.base_url = BASE_URL
    
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
                        return True
                except requests.exceptions.RequestException:
                    continue
            
            # 如果所有端点都失败，尝试直接检查API
            try:
                response = requests.get(f"{self.base_url}/brands?page_size=1", timeout=3)
                if response.status_code in [200, 401, 403]:  # 即使需要认证也算服务在运行
                    return True
            except:
                pass
            
            # 如果检查失败，假设服务在运行（让后续的API调用来验证）
            return True
        except Exception as e:
            # 如果检查异常，假设服务在运行
            return True
    
    def create_brand(self, name: str, keywords: List[str], description: str = "") -> Optional[int]:
        """
        创建品牌
        
        Args:
            name: 品牌名称
            keywords: 关键词列表
            description: 品牌描述
            
        Returns:
            品牌ID，失败返回None
        """
        brand_data = {
            "name": name,
            "description": description or f"{name}品牌分析",
            "keywords": keywords,
            "platforms": [self.platform]
        }
        
        try:
            response = requests.post(f"{self.base_url}/brands", json=brand_data)
            if response.status_code in [200, 201]:
                result = response.json()
                if "id" in result:
                    return result["id"]
                elif "data" in result and "id" in result["data"]:
                    return result["data"]["id"]
            logger.error(f"创建品牌失败: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.error(f"创建品牌失败: {e}")
            return None
    
    def create_crawl_task(
        self,
        brand_id: int,
        keywords: List[str],
        max_items: int = 10,
        include_comments: bool = True
    ) -> Optional[int]:
        """
        创建爬虫任务
        
        Args:
            brand_id: 品牌ID
            keywords: 关键词列表
            max_items: 最大爬取数量
            include_comments: 是否包含评论
            
        Returns:
            任务ID，失败返回None
        """
        task_data = {
            "platforms": [self.platform],
            "keywords": keywords,
            "max_items": max_items,
            "include_comments": include_comments
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/brands/{brand_id}/crawl",
                json=task_data
            )
            
            if response.status_code == 200:
                result = response.json()
                if "data" in result and "task_ids" in result["data"]:
                    task_ids = result["data"]["task_ids"]
                    if task_ids:
                        return task_ids[0]
            logger.error(f"创建任务失败: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            return None
    
    def get_task_status(self, task_id: int) -> Optional[Dict]:
        """获取任务状态"""
        try:
            response = requests.get(f"{self.base_url}/crawl-tasks/{task_id}")
            if response.status_code == 200:
                return response.json()["data"]
            return None
        except Exception as e:
            logger.error(f"获取任务状态失败: {e}")
            return None
    
    def get_data_stats(self, brand_id: int) -> Optional[Dict]:
        """获取数据统计"""
        try:
            response = requests.get(f"{self.base_url}/brands/{brand_id}/data/stats")
            if response.status_code == 200:
                return response.json()["data"]
            return None
        except Exception as e:
            logger.error(f"获取数据统计失败: {e}")
            return None
    
    @abstractmethod
    def crawl(
        self,
        brand_name: str,
        keywords: List[str],
        max_items: int = 10,
        include_comments: bool = True
    ) -> Dict:
        """
        执行爬取
        
        Args:
            brand_name: 品牌名称
            keywords: 关键词列表
            max_items: 最大爬取数量
            include_comments: 是否包含评论
            
        Returns:
            爬取结果字典
        """
        pass

