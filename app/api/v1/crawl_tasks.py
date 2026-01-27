"""
数据采集API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

from app.core.database import get_db
from app.models.brand import Brand
from app.models.crawl_task import CrawlTask, TaskStatus, CrawlType

router = APIRouter()


# 请求模型
class CrawlTaskCreate(BaseModel):
    platforms: List[str]
    keywords: Optional[List[str]] = None
    crawl_type: str = "search"  # search/creator/detail
    target_url: Optional[str] = None # 目标链接
    max_items: int = 100
    include_comments: bool = True
    download_media: bool = True  # 新增字段，默认开启


class CrawlTaskResponse(BaseModel):
    id: int
    brand_id: int
    platform: str
    crawl_type: str
    status: str
    keyword: Optional[str]
    target_url: Optional[str]
    total_items: int
    crawled_items: int
    progress: int
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    
    class Config:
        from_attributes = True


@router.post("/brands/{brand_id}/crawl", response_model=dict)
async def start_crawl(
    brand_id: int,
    task_data: CrawlTaskCreate,
    db: Session = Depends(get_db)
):
    """启动爬虫任务"""
    # 检查品牌是否存在
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="品牌不存在")
    
    # 参数验证
    if task_data.crawl_type == "search" and not task_data.keywords:
         raise HTTPException(status_code=400, detail="关键词搜索模式必须提供关键词")
    
    if task_data.crawl_type in ["creator", "detail"] and not task_data.target_url:
         raise HTTPException(status_code=400, detail=f"指定{task_data.crawl_type}模式必须提供目标链接")

    # 为每个平台创建爬虫任务
    tasks = []
    
    # 如果是 search 模式，可能包含多个关键词
    if task_data.crawl_type == "search":
        for platform in task_data.platforms:
            for keyword in task_data.keywords:
                task = CrawlTask(
                    brand_id=brand_id,
                    platform=platform,
                    crawl_type=CrawlType.SEARCH,
                    keyword=keyword,
                    max_items=task_data.max_items,
                    download_media=1 if task_data.download_media else 0,
                    status=TaskStatus.PENDING
                )
                db.add(task)
                tasks.append(task)
    else:
        # 如果是 creator/detail 模式，通常只针对单一目标链接
        # 如果有多个平台（虽然通常一个链接只对应一个平台），这里还是保留循环
        for platform in task_data.platforms:
             task = CrawlTask(
                brand_id=brand_id,
                platform=platform,
                crawl_type=CrawlType(task_data.crawl_type),
                target_url=task_data.target_url,
                max_items=task_data.max_items,
                download_media=1 if task_data.download_media else 0,
                status=TaskStatus.PENDING
            )
             db.add(task)
             tasks.append(task)
    
    db.commit()
    
    # 刷新任务以获取ID
    for task in tasks:
        db.refresh(task)
    
    # 异步启动爬虫任务（使用Celery）
    try:
        from app.tasks.crawl_tasks import crawl_brand_task
        for task in tasks:
            crawl_brand_task.delay(task.id)
        logger.info(f"已启动 {len(tasks)} 个爬虫任务")
    except Exception as e:
        logger.error(f"启动爬虫任务失败: {e}")
        # 如果Celery未配置，任务仍会创建，但不会自动执行
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "task_ids": [task.id for task in tasks],
            "brand_id": brand_id,
            "platforms": task_data.platforms,
            "status": "pending"
        }
    }


@router.get("/crawl-tasks", response_model=dict)
async def get_crawl_tasks(
    brand_id: Optional[int] = Query(None),
    status: Optional[TaskStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取爬虫任务列表"""
    query = db.query(CrawlTask)
    
    if brand_id:
        query = query.filter(CrawlTask.brand_id == brand_id)
    if status:
        query = query.filter(CrawlTask.status == status)
    
    total = query.count()
    items = query.order_by(CrawlTask.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": [
                CrawlTaskResponse(
                    id=item.id,
                    brand_id=item.brand_id,
                    platform=item.platform,
                    crawl_type=item.crawl_type.value if hasattr(item.crawl_type, "value") else str(item.crawl_type),
                    status=item.status.value,
                    keyword=item.keyword,
                    target_url=item.target_url,
                    total_items=item.total_items,
                    crawled_items=item.crawled_items,
                    progress=item.progress,
                    created_at=item.created_at.isoformat(),
                    started_at=item.started_at.isoformat() if item.started_at else None,
                    completed_at=item.completed_at.isoformat() if item.completed_at else None
                ).model_dump()
                for item in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


@router.get("/crawl-tasks/{task_id}", response_model=dict)
async def get_crawl_task(task_id: int, db: Session = Depends(get_db)):
    """获取爬虫任务详情"""
    task = db.query(CrawlTask).filter(CrawlTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "code": 200,
        "message": "success",
        "data": CrawlTaskResponse(
            id=task.id,
            brand_id=task.brand_id,
            platform=task.platform,
            crawl_type=task.crawl_type.value if hasattr(task.crawl_type, "value") else str(task.crawl_type),
            status=task.status.value,
            keyword=task.keyword,
            target_url=task.target_url,
            total_items=task.total_items,
            crawled_items=task.crawled_items,
            progress=task.progress,
            created_at=task.created_at.isoformat(),
            started_at=task.started_at.isoformat() if task.started_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None
        ).model_dump()
    }
