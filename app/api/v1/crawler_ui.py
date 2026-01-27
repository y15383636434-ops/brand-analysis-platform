"""
爬虫Web界面API
提供Web界面用于选择平台和爬取方式
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from crawlers import (
    XHSCrawler,
    DouyinCrawler,
    WeiboCrawler,
    ZhihuCrawler,
    BilibiliCrawler,
    KuaishouCrawler
)

router = APIRouter()

# 模板目录
templates_dir = project_root / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# 平台映射
PLATFORM_MAP = {
    "xhs": ("小红书", XHSCrawler),
    "douyin": ("抖音", DouyinCrawler),
    "weibo": ("微博", WeiboCrawler),
    "zhihu": ("知乎", ZhihuCrawler),
    "bilibili": ("B站", BilibiliCrawler),
    "kuaishou": ("快手", KuaishouCrawler),
}


@router.get("/crawler", response_class=HTMLResponse)
async def crawler_ui(request: Request):
    """爬虫选择界面"""
    platforms = [
        {"code": code, "name": name}
        for code, (name, _) in PLATFORM_MAP.items()
    ]
    return templates.TemplateResponse("crawler_ui.html", {
        "request": request,
        "platforms": platforms
    })


@router.post("/crawler/start")
async def start_crawl(
    platforms: str = Form(...),  # 改为接收多个平台，用逗号分隔
    brand_name: str = Form(...),
    keywords: str = Form(...),
    max_items: int = Form(10),
    include_comments: bool = Form(True),
    download_media: bool = Form(True)
):
    """启动爬虫任务（支持多平台）"""
    # 解析平台列表
    platform_list = [p.strip() for p in platforms.split(",") if p.strip()]
    if not platform_list:
        return {
            "success": False,
            "error": "请至少选择一个平台"
        }
    
    # 验证平台
    invalid_platforms = [p for p in platform_list if p not in PLATFORM_MAP]
    if invalid_platforms:
        return {
            "success": False,
            "error": f"无效的平台: {', '.join(invalid_platforms)}"
        }
    
    # 解析关键词
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    if not keyword_list:
        return {
            "success": False,
            "error": "关键词不能为空"
        }
    
    try:
        # 使用多平台爬虫
        from crawlers.multi_platform_crawler import MultiPlatformCrawler
        
        crawler = MultiPlatformCrawler()
        result = crawler.crawl_multiple_platforms(
            platforms=platform_list,
            brand_name=brand_name,
            keywords=keyword_list,
            max_items=max_items,
            include_comments=include_comments,
            download_media=download_media
        )
        
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

