"""
品牌管理API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_async_db
from app.models.brand import BrandStatus
from app.services.brand_service import BrandService
from app.models.data_import_task import DataImportTask
from app.tasks.import_tasks import import_brand_data_task
from app.models.crawl_task import TaskStatus
from sqlalchemy import func
from loguru import logger

router = APIRouter()


# 请求模型
class BrandCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    keywords: List[str] = []
    platforms: List[str] = []


class BrandUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    platforms: Optional[List[str]] = None
    status: Optional[BrandStatus] = None


class BrandResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    keywords: List[str]
    platforms: List[str]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/brands", response_model=BrandResponse, status_code=201)
async def create_brand(brand_data: BrandCreate, db: AsyncSession = Depends(get_async_db)):
    """创建品牌"""
    service = BrandService(db)
    brand = await service.create(
        name=brand_data.name,
        description=brand_data.description,
        keywords=brand_data.keywords,
        platforms=brand_data.platforms
    )
    return brand


@router.get("/brands", response_model=dict)
async def get_brands(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[BrandStatus] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """获取品牌列表"""
    service = BrandService(db)
    items, total = await service.get_list(page=page, page_size=page_size, status=status)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": [BrandResponse.model_validate(item).model_dump() for item in items],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


@router.get("/brands/{brand_id}", response_model=dict)
async def get_brand(brand_id: int, db: AsyncSession = Depends(get_async_db)):
    """获取品牌详情"""
    service = BrandService(db)
    brand = await service.get(brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="品牌不存在")
    
    return {
        "code": 200,
        "message": "success",
        "data": BrandResponse.model_validate(brand).model_dump()
    }


@router.put("/brands/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: int,
    brand_data: BrandUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """更新品牌"""
    service = BrandService(db)
    
    # 转换为字典并过滤None值
    update_data = {k: v for k, v in brand_data.model_dump().items() if v is not None}
    
    brand = await service.update(brand_id, **update_data)
    if not brand:
        raise HTTPException(status_code=404, detail="品牌不存在")
    
    return brand


@router.delete("/brands/{brand_id}")
async def delete_brand(brand_id: int, db: AsyncSession = Depends(get_async_db)):
    """删除品牌"""
    service = BrandService(db)
    logger.info(f"开始删除品牌 ID={brand_id}")
    
    try:
        success = await service.delete(brand_id)
        if not success:
            logger.warning(f"品牌不存在 ID={brand_id}")
            raise HTTPException(status_code=404, detail="品牌不存在")
        
        logger.info(f"成功删除品牌 ID={brand_id}")
        return Response(status_code=204)
    except Exception as e:
        logger.error(f"删除品牌失败: {e}")
        # 如果是HTTPException，直接抛出
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/data/files", response_model=dict)
async def list_available_data_files(
    platform: Optional[str] = Query(None, description="平台筛选"),
    keyword: Optional[str] = Query(None, description="关键词筛选")
):
    """
    获取可关联的JSON数据文件列表
    """
    try:
        from pathlib import Path
        from config import settings
        
        # 1. 确定扫描目录
        # 包括 MediaCrawler 原生目录和项目的 crawled_data 目录
        scan_dirs = []
        
        # MediaCrawler 目录
        mediacrawler_path = settings.MEDIACRAWLER_PATH
        if mediacrawler_path:
            mediacrawler_path = Path(mediacrawler_path).resolve()
            if mediacrawler_path.exists():
                scan_dirs.append(mediacrawler_path / "data")
        
        # 项目目录
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        crawled_data_dir = project_root / "data" / "crawled_data"
        if crawled_data_dir.exists():
            scan_dirs.append(crawled_data_dir)
            
        json_files = []
        for d in scan_dirs:
            if d.exists():
                json_files.extend(list(d.rglob("*.json")))
                
        # 2. 处理文件信息
        files_info = []
        for file_path in json_files:
            try:
                # 简单的平台和关键词判断
                filename = file_path.name.lower()
                
                # 平台过滤
                file_platform = "unknown"
                if "xhs" in filename: file_platform = "xhs"
                elif "douyin" in filename or "dy" in filename: file_platform = "douyin"
                elif "bili" in filename: file_platform = "bilibili"
                elif "weibo" in filename or "wb" in filename: file_platform = "weibo"
                elif "tieba" in filename: file_platform = "tieba"
                elif "zhihu" in filename: file_platform = "zhihu"
                elif "kuaishou" in filename or "ks" in filename: file_platform = "kuaishou"
                
                if platform and platform != file_platform:
                    continue
                    
                # 关键词过滤
                if keyword and keyword.lower() not in filename:
                    continue
                
                stat = file_path.stat()
                files_info.append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "size": stat.st_size,
                    "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "platform": file_platform
                })
            except Exception as e:
                logger.error(f"读取文件 {file_path} 失败: {e}")
                
        # 按修改时间倒序
        files_info.sort(key=lambda x: x["modified_time"], reverse=True)
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "total": len(files_info),
                "items": files_info
            }
        }
        
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")


@router.post("/brands/{brand_id}/import-files", response_model=dict)
async def import_specific_files(
    brand_id: int, 
    files: List[str],
    db: AsyncSession = Depends(get_async_db)
):
    """
    导入指定的JSON文件到品牌 (异步任务)
    
    Args:
        brand_id: 品牌ID
        files: 文件路径列表
    """
    # 检查品牌是否存在
    service = BrandService(db)
    brand = await service.get(brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="品牌不存在")
        
    if not files:
        raise HTTPException(status_code=400, detail="未选择任何文件")
    
    try:
        # 创建导入任务记录
        import_task = DataImportTask(
            brand_id=brand_id,
            file_list=files,
            total_files=len(files),
            status=TaskStatus.PENDING
        )
        db.add(import_task)
        await db.commit()
        await db.refresh(import_task)
        
        # 启动Celery任务
        task_result = import_brand_data_task.delay(import_task.id)
        
        # 更新Celery任务ID
        import_task.celery_task_id = task_result.id
        await db.commit()
        
        return {
            "code": 200,
            "message": "已启动导入任务",
            "data": {
                "import_task_id": import_task.id,
                "brand_id": brand_id,
                "file_count": len(files),
                "status": TaskStatus.PENDING.value
            }
        }
        
    except Exception as e:
        logger.error(f"启动导入任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动导入任务失败: {str(e)}")


@router.get("/brands/{brand_id}/import-tasks", response_model=dict)
async def get_import_tasks(
    brand_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    """获取品牌导入任务列表"""
    from sqlalchemy import select, desc
    
    try:
        # 查询任务
        stmt = select(DataImportTask).where(
            DataImportTask.brand_id == brand_id
        ).order_by(desc(DataImportTask.created_at)).offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(stmt)
        tasks = result.scalars().all()
        
        # 获取总数
        count_stmt = select(func.count()).select_from(DataImportTask).where(DataImportTask.brand_id == brand_id)
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "items": [
                    {
                        "id": task.id,
                        "status": task.status.value if hasattr(task.status, "value") else str(task.status),
                        "created_at": task.created_at.isoformat() if task.created_at else None,
                        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                        "total_files": task.total_files,
                        "processed_files": task.processed_files,
                        "imported_items": task.imported_items,
                        "skipped_items": task.skipped_items,
                        "error_message": task.error_message
                    } for task in tasks
                ],
                "total": total,
                "page": page,
                "page_size": page_size
            }
        }
    except Exception as e:
        logger.error(f"获取导入任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")
