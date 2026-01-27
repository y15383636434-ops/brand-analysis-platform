"""
数据导入Celery任务
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime
from celery import Task
from loguru import logger
from sqlalchemy.orm import Session
from pymongo import MongoClient

from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.data_import_task import DataImportTask
from app.models.crawl_task import TaskStatus
from config import settings

@celery_app.task(bind=True, name="import_brand_data_task")
def import_brand_data_task(self: Task, import_task_id: int):
    """
    导入品牌数据任务
    
    Args:
        import_task_id: 导入任务ID
    """
    db: Session = SessionLocal()
    mongo_client = None
    
    try:
        # 获取任务
        task = db.query(DataImportTask).filter(DataImportTask.id == import_task_id).first()
        if not task:
            logger.error(f"导入任务不存在: {import_task_id}")
            return {"error": "导入任务不存在"}
        
        # 更新任务状态
        task.status = TaskStatus.RUNNING
        task.celery_task_id = self.request.id
        task.started_at = datetime.now()
        db.commit()
        
        logger.info(f"开始导入任务: {import_task_id}, 品牌ID: {task.brand_id}")
        
        # 连接MongoDB
        mongo_client = MongoClient(
            host=settings.MONGODB_HOST,
            port=settings.MONGODB_PORT,
            serverSelectionTimeoutMS=2000
        )
        mongodb = mongo_client[settings.MONGODB_DATABASE]
        collection = mongodb.raw_data
        
        files = task.file_list or []
        task.total_files = len(files)
        db.commit()
        
        imported_count = 0
        skipped_count = 0
        processed_files = 0
        
        for file_str in files:
            file_path = Path(file_str)
            if not file_path.exists():
                logger.warning(f"文件不存在: {file_path}")
                processed_files += 1
                task.processed_files = processed_files
                db.commit()
                continue
                
            try:
                # 确定平台
                filename = file_path.name.lower()
                platform = "unknown"
                if "xhs" in filename: platform = "xhs"
                elif "douyin" in filename or "dy" in filename: platform = "douyin"
                elif "bili" in filename: platform = "bilibili"
                elif "weibo" in filename or "wb" in filename: platform = "weibo"
                elif "tieba" in filename: platform = "tieba"
                elif "zhihu" in filename: platform = "zhihu"
                elif "kuaishou" in filename or "ks" in filename: platform = "kuaishou"
                
                # 读取文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                items = []
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    if "items" in data:
                        items = data["items"]
                    elif "data" in data and isinstance(data["data"], list):
                        items = data["data"]
                    else:
                        items = [data]
                
                # 过滤有效数据
                real_items = [item for item in items if isinstance(item, dict) and (item.get("id") or item.get("aweme_id") or item.get("title") or item.get("content") or item.get("desc"))]
                
                for item in real_items:
                    content_id = item.get("id") or item.get("aweme_id") or item.get("note_id") or ""
                    title = item.get("title") or item.get("desc") or ""
                    content = item.get("content") or item.get("desc") or item.get("text") or ""
                    
                    if not content_id:
                        unique_str = f"{title}{content[:100]}"
                        content_id = hashlib.md5(unique_str.encode()).hexdigest()
                    
                    doc = {
                        "brand_id": task.brand_id,
                        "platform": platform,
                        "content_id": str(content_id),
                        "title": title,
                        "content": content,
                        "raw_data": item,
                        "crawled_at": datetime.now(),
                        "source_file": str(file_path.name)
                    }
                    
                    # 查重
                    existing = collection.find_one({
                        "brand_id": task.brand_id,
                        "content_id": str(content_id),
                        "platform": platform
                    })
                    
                    if not existing:
                        collection.insert_one(doc)
                        imported_count += 1
                    else:
                        skipped_count += 1
                
                # 更新文件进度
                processed_files += 1
                task.processed_files = processed_files
                task.imported_items = imported_count
                task.skipped_items = skipped_count
                db.commit()
                
            except Exception as e:
                logger.error(f"处理文件失败 {file_path}: {e}")
                # 继续处理下一个文件
                processed_files += 1
                task.processed_files = processed_files
                db.commit()
        
        # 任务完成
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        db.commit()
        
        return {
            "status": "completed",
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "processed_files": processed_files
        }
        
    except Exception as e:
        logger.error(f"导入任务异常: {e}", exc_info=True)
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            db.commit()
        return {"error": str(e)}
        
    finally:
        if mongo_client:
            mongo_client.close()
        db.close()
