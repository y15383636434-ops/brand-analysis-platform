"""
微博爬虫
"""
import sys
from pathlib import Path
from typing import Dict, List

# 添加项目根目录到路径，支持直接运行
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from .base_crawler import BaseCrawler
except ImportError:
    # 如果相对导入失败，使用绝对导入
    from crawlers.base_crawler import BaseCrawler


class WeiboCrawler(BaseCrawler):
    """微博爬虫"""
    
    def __init__(self):
        super().__init__("weibo")
        self.platform_name = "微博"
    
    def crawl(self, brand_name: str, keywords: List[str], max_items: int = 10, include_comments: bool = True) -> Dict:
        """执行微博爬取（使用XHSCrawler的逻辑）"""
        try:
            from .xhs_crawler import XHSCrawler
        except ImportError:
            from crawlers.xhs_crawler import XHSCrawler
        
        xhs_crawler = XHSCrawler()
        xhs_crawler.platform = "weibo"
        xhs_crawler.platform_name = "微博"
        return xhs_crawler.crawl(brand_name, keywords, max_items, include_comments)


if __name__ == "__main__":
    # 测试代码
    print("="*60)
    print("微博爬虫测试")
    print("="*60)
    
    crawler = WeiboCrawler()
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

