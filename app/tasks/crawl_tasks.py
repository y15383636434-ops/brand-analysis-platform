"""
爬虫异步任务
"""
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger

from app.tasks.celery_app import celery_app
from app.models.crawl_task import CrawlTask, TaskStatus
from app.services.crawler_service import CrawlerService
from config import settings
from app.core.database import get_mongodb

# 创建数据库会话（用于Celery任务）
SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
    f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
    f"?charset=utf8mb4"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    """获取数据库会话（用于Celery任务）"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # 不在这里关闭，让调用者关闭


@celery_app.task(bind=True, name="crawl_brand_task")
def crawl_brand_task(self, task_id: int):
    """
    爬虫任务
    
    Args:
        task_id: 爬虫任务ID
    """
    db = get_db_session()
    crawler_service = CrawlerService()
    mongodb = get_mongodb()
    
    try:
        # 获取任务
        task = db.query(CrawlTask).filter(CrawlTask.id == task_id).first()
        if not task:
            logger.error(f"任务 {task_id} 不存在")
            return {"status": "failed", "error": "任务不存在"}
        
        # 更新任务状态为运行中
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        db.commit()
        
        logger.info(f"开始执行爬虫任务 {task_id}: 平台={task.platform}, 关键词={task.keyword}")
        
        # 执行爬取
        keywords = [task.keyword] if task.keyword else []
        crawl_result = crawler_service.crawl_platform(
            platform=task.platform,
            keywords=keywords,
            max_items=task.max_items,
            include_comments=True,
            crawl_type=task.crawl_type.value if hasattr(task.crawl_type, "value") else str(task.crawl_type),
            target_url=task.target_url,
            enable_media_download=bool(task.download_media)
        )
        
        # 更新进度
        total_items = crawl_result.get("total_items", 0)
        task.total_items = total_items
        task.crawled_items = total_items
        task.progress = 100
        
        # 保存数据到MongoDB
        if crawl_result.get("items"):
            saved_count = crawler_service.save_crawled_data(
                brand_id=task.brand_id,
                task_id=task_id,
                platform=task.platform,
                data=crawl_result,
                mongodb=mongodb
            )
            task.crawled_items = saved_count
        else:
            saved_count = 0
        
        # 更新任务状态为完成
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        if task.started_at:
            task.duration = int((task.completed_at - task.started_at).total_seconds())
        
        db.commit()
        
        logger.info(f"爬虫任务 {task_id} 完成: 采集 {total_items} 条，保存 {saved_count} 条")
        
        return {
            "status": "completed",
            "task_id": task_id,
            "total_items": total_items,
            "saved_items": saved_count
        }
        
    except Exception as e:
        logger.error(f"爬虫任务 {task_id} 失败: {e}", exc_info=True)
        
        # 更新任务状态为失败
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            if task.started_at:
                task.duration = int((task.completed_at - task.started_at).total_seconds())
            db.commit()
        
        return {
            "status": "failed",
            "task_id": task_id,
            "error": str(e)
        }
    finally:
        db.close()






