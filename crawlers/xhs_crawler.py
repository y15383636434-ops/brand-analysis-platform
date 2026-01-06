"""
小红书爬虫
"""
import sys
import time
from pathlib import Path
from typing import Dict, List
from loguru import logger

# 添加项目根目录到路径，支持直接运行
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from .base_crawler import BaseCrawler
except ImportError:
    # 如果相对导入失败，使用绝对导入
    from crawlers.base_crawler import BaseCrawler


class XHSCrawler(BaseCrawler):
    """小红书爬虫"""
    
    def __init__(self):
        super().__init__("xhs")
        self.platform_name = "小红书"
    
    def crawl(
        self,
        brand_name: str,
        keywords: List[str],
        max_items: int = 10,
        include_comments: bool = True
    ) -> Dict:
        """
        执行小红书爬取
        
        Args:
            brand_name: 品牌名称
            keywords: 关键词列表
            max_items: 最大爬取数量
            include_comments: 是否包含评论
            
        Returns:
            爬取结果字典
        """
        print("="*60)
        print(f"{self.platform_name}爬虫")
        print("="*60)
        print(f"品牌名称: {brand_name}")
        print(f"关键词: {', '.join(keywords)}")
        print(f"最大数量: {max_items}")
        print(f"包含评论: {include_comments}")
        print()
        
        # 检查服务（如果检查失败，继续尝试，让实际API调用来验证）
        service_ok = self.check_service()
        if service_ok:
            print("[OK] 服务运行正常\n")
        else:
            print("[!] 服务检查失败，但将继续尝试...\n")
        
        # 创建品牌
        print("1. 创建品牌...")
        brand_id = self.create_brand(brand_name, keywords)
        if not brand_id:
            return {
                "success": False,
                "error": "创建品牌失败"
            }
        print(f"[OK] 品牌创建成功，ID: {brand_id}\n")
        
        # 创建爬虫任务
        print("2. 创建爬虫任务...")
        task_id = self.create_crawl_task(
            brand_id=brand_id,
            keywords=keywords,
            max_items=max_items,
            include_comments=include_comments
        )
        if not task_id:
            return {
                "success": False,
                "error": "创建爬虫任务失败"
            }
        print(f"[OK] 爬虫任务创建成功，任务ID: {task_id}\n")
        
        # 等待任务执行
        print("3. 等待任务执行...")
        print("   提示: 任务在后台执行，请查看Celery Worker窗口")
        print("   首次使用可能需要扫码登录\n")
        
        # 轮询任务状态
        max_wait_time = 300  # 最大等待5分钟
        check_interval = 10  # 每10秒检查一次
        waited_time = 0
        
        while waited_time < max_wait_time:
            time.sleep(check_interval)
            waited_time += check_interval
            
            task = self.get_task_status(task_id)
            if task:
                status = task.get("status")
                progress = task.get("progress", 0)
                crawled = task.get("crawled_items", 0)
                total = task.get("total_items", 0)
                
                print(f"   已等待 {waited_time} 秒 - 状态: {status}, 进度: {progress}%, 已爬取: {crawled}/{total}")
                
                if status == "completed":
                    print("\n[OK] 任务完成！\n")
                    break
                elif status == "failed":
                    error_msg = task.get("error_message", "未知错误")
                    return {
                        "success": False,
                        "error": f"任务失败: {error_msg}",
                        "task_id": task_id,
                        "brand_id": brand_id
                    }
        
        # 获取数据统计
        print("4. 查看数据统计...")
        stats = self.get_data_stats(brand_id)
        if stats:
            total = stats.get("total", 0)
            print(f"   总数据: {total} 条")
            if "platforms" in stats:
                for p in stats["platforms"]:
                    print(f"   {p.get('_id')}: {p.get('count')} 条")
        
        print("\n" + "="*60)
        print("爬取完成！")
        print("="*60)
        print(f"\n查看数据:")
        print(f"  - 数据列表: GET {self.base_url}/brands/{brand_id}/data")
        print(f"  - 数据统计: GET {self.base_url}/brands/{brand_id}/data/stats")
        print(f"  - API文档: http://localhost:8000/docs")
        
        return {
            "success": True,
            "brand_id": brand_id,
            "task_id": task_id,
            "platform": self.platform,
            "stats": stats
        }


if __name__ == "__main__":
    # 测试代码
    print("="*60)
    print("小红书爬虫测试")
    print("="*60)
    
    crawler = XHSCrawler()
    result = crawler.crawl(
        brand_name="测试品牌",
        keywords=["华为", "小米"],
        max_items=5,
        include_comments=False
    )
    
    print("\n测试结果:")
    print(f"成功: {result.get('success', False)}")
    if result.get('success'):
        print(f"品牌ID: {result.get('brand_id')}")
        print(f"任务ID: {result.get('task_id')}")
    else:
        print(f"错误: {result.get('error', '未知错误')}")

