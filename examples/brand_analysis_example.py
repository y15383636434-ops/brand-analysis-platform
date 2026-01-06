"""
品牌分析系统 - 使用示例

这个示例展示了如何使用品牌分析系统来分析"山四砂锅"这个品牌
"""

import asyncio
import requests
from typing import Dict, List

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"


class BrandAnalysisClient:
    """品牌分析系统客户端"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def create_brand(self, name: str, description: str = "", 
                    keywords: List[str] = None, 
                    platforms: List[str] = None) -> Dict:
        """创建品牌"""
        if keywords is None:
            keywords = [name]
        if platforms is None:
            platforms = ["xhs", "douyin", "weibo", "zhihu"]
        
        data = {
            "name": name,
            "description": description,
            "keywords": keywords,
            "platforms": platforms
        }
        
        response = self.session.post(
            f"{self.base_url}/brands",
            json=data
        )
        return response.json()
    
    def start_crawl(self, brand_id: int, platforms: List[str] = None,
                   keywords: List[str] = None, max_items: int = 100) -> Dict:
        """启动爬虫任务"""
        if platforms is None:
            platforms = ["xhs", "douyin", "weibo", "zhihu"]
        if keywords is None:
            # 从品牌信息获取关键词
            brand_info = self.get_brand(brand_id)
            keywords = brand_info.get("data", {}).get("keywords", [])
        
        data = {
            "platforms": platforms,
            "keywords": keywords,
            "max_items": max_items,
            "include_comments": True
        }
        
        response = self.session.post(
            f"{self.base_url}/brands/{brand_id}/crawl",
            json=data
        )
        return response.json()
    
    def get_brand(self, brand_id: int) -> Dict:
        """获取品牌信息"""
        response = self.session.get(f"{self.base_url}/brands/{brand_id}")
        return response.json()
    
    def wait_for_task(self, task_id: int, task_type: str = "crawl", 
                     timeout: int = 3600) -> Dict:
        """等待任务完成"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if task_type == "crawl":
                response = self.session.get(
                    f"{self.base_url}/crawl-tasks/{task_id}"
                )
            elif task_type == "analyze":
                response = self.session.get(
                    f"{self.base_url}/analysis-tasks/{task_id}"
                )
            else:
                raise ValueError(f"Unknown task type: {task_type}")
            
            task_data = response.json()
            status = task_data.get("data", {}).get("status")
            
            if status == "completed":
                return task_data
            elif status == "failed":
                raise Exception(f"Task failed: {task_data}")
            
            print(f"任务 {task_id} 状态: {status}, 等待中...")
            time.sleep(5)
        
        raise TimeoutError(f"Task {task_id} timeout after {timeout} seconds")
    
    def start_analysis(self, brand_id: int, analysis_type: str = "full") -> Dict:
        """启动分析任务"""
        data = {
            "analysis_type": analysis_type,
            "include_sentiment": True,
            "include_topics": True,
            "include_keywords": True,
            "include_insights": True
        }
        
        response = self.session.post(
            f"{self.base_url}/brands/{brand_id}/analyze",
            json=data
        )
        return response.json()
    
    def get_analysis(self, brand_id: int) -> Dict:
        """获取分析结果"""
        response = self.session.get(
            f"{self.base_url}/brands/{brand_id}/analysis"
        )
        return response.json()
    
    def generate_report(self, brand_id: int, format: str = "pdf") -> Dict:
        """生成报告"""
        data = {
            "report_type": "full",
            "format": format,
            "include_charts": True,
            "language": "zh-CN"
        }
        
        response = self.session.post(
            f"{self.base_url}/brands/{brand_id}/reports",
            json=data
        )
        return response.json()
    
    def download_report(self, report_id: int, save_path: str):
        """下载报告"""
        response = self.session.get(
            f"{self.base_url}/reports/{report_id}/download",
            stream=True
        )
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"报告已保存到: {save_path}")


def analyze_brand_example():
    """完整的品牌分析示例"""
    client = BrandAnalysisClient()
    
    print("=" * 50)
    print("品牌分析系统 - 使用示例")
    print("=" * 50)
    
    # 1. 创建品牌
    print("\n1. 创建品牌: 山四砂锅")
    brand_result = client.create_brand(
        name="山四砂锅",
        description="传统砂锅品牌，专注于高品质砂锅产品",
        keywords=["山四砂锅", "山四", "砂锅", "传统砂锅"],
        platforms=["xhs", "douyin", "weibo", "zhihu"]
    )
    
    if brand_result.get("code") != 200:
        print(f"创建品牌失败: {brand_result}")
        return
    
    brand_id = brand_result["data"]["id"]
    print(f"✓ 品牌创建成功，ID: {brand_id}")
    
    # 2. 启动数据采集
    print("\n2. 启动数据采集任务...")
    crawl_result = client.start_crawl(
        brand_id=brand_id,
        platforms=["xhs", "douyin", "weibo"],
        keywords=["山四砂锅"],
        max_items=100
    )
    
    if crawl_result.get("code") != 200:
        print(f"启动爬虫失败: {crawl_result}")
        return
    
    crawl_task_id = crawl_result["data"]["task_id"]
    print(f"✓ 爬虫任务已启动，任务ID: {crawl_task_id}")
    
    # 3. 等待爬虫完成
    print("\n3. 等待数据采集完成...")
    try:
        task_result = client.wait_for_task(crawl_task_id, task_type="crawl")
        print("✓ 数据采集完成")
        print(f"  采集数据量: {task_result['data']['crawled_items']}")
    except Exception as e:
        print(f"✗ 数据采集失败: {e}")
        return
    
    # 4. 启动AI分析
    print("\n4. 启动AI分析任务...")
    analysis_result = client.start_analysis(
        brand_id=brand_id,
        analysis_type="full"
    )
    
    if analysis_result.get("code") != 200:
        print(f"启动分析失败: {analysis_result}")
        return
    
    analysis_task_id = analysis_result["data"]["task_id"]
    print(f"✓ 分析任务已启动，任务ID: {analysis_task_id}")
    
    # 5. 等待分析完成
    print("\n5. 等待AI分析完成...")
    try:
        task_result = client.wait_for_task(analysis_task_id, task_type="analyze")
        print("✓ AI分析完成")
    except Exception as e:
        print(f"✗ AI分析失败: {e}")
        return
    
    # 6. 获取分析结果
    print("\n6. 获取分析结果...")
    analysis_data = client.get_analysis(brand_id)
    
    if analysis_data.get("code") == 200:
        data = analysis_data["data"]
        print("✓ 分析结果:")
        print(f"  情感分析 - 正面: {data['sentiment_analysis']['positive']}%")
        print(f"  情感分析 - 负面: {data['sentiment_analysis']['negative']}%")
        print(f"  主题数量: {len(data['topics'])}")
        print(f"  关键词数量: {len(data['keywords'])}")
        print(f"\n  核心洞察:\n  {data['insights'][:200]}...")
    
    # 7. 生成报告
    print("\n7. 生成分析报告...")
    report_result = client.generate_report(
        brand_id=brand_id,
        format="pdf"
    )
    
    if report_result.get("code") == 200:
        report_id = report_result["data"]["report_id"]
        print(f"✓ 报告生成任务已启动，报告ID: {report_id}")
        
        # 等待报告生成完成（实际应用中应该使用WebSocket或轮询）
        import time
        time.sleep(10)  # 假设报告生成需要10秒
        
        # 下载报告
        save_path = f"brand_report_{brand_id}.pdf"
        client.download_report(report_id, save_path)
        print(f"✓ 报告已下载: {save_path}")
    
    print("\n" + "=" * 50)
    print("品牌分析完成！")
    print("=" * 50)


if __name__ == "__main__":
    # 运行示例
    analyze_brand_example()

