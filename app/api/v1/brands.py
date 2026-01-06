"""
品牌管理API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.brand import Brand, BrandStatus

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
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


@router.post("/brands", response_model=BrandResponse, status_code=201)
async def create_brand(brand_data: BrandCreate, db: Session = Depends(get_db)):
    """创建品牌"""
    # 检查品牌是否已存在（可选：如果用户想允许同名品牌，可以注释掉这部分）
    existing_brand = db.query(Brand).filter(Brand.name == brand_data.name).first()
    if existing_brand:
        # 返回已存在的品牌信息，而不是报错
        return BrandResponse(
            id=existing_brand.id,
            name=existing_brand.name,
            description=existing_brand.description,
            keywords=existing_brand.keywords or [],
            platforms=existing_brand.platforms or [],
            status=existing_brand.status.value,
            created_at=existing_brand.created_at.isoformat(),
            updated_at=existing_brand.updated_at.isoformat()
        )
    
    # 创建品牌
    brand = Brand(
        name=brand_data.name,
        description=brand_data.description,
        keywords=brand_data.keywords or [brand_data.name],
        platforms=brand_data.platforms or ["xhs", "douyin", "weibo", "zhihu"]
    )
    
    db.add(brand)
    db.commit()
    db.refresh(brand)
    
    return BrandResponse(
        id=brand.id,
        name=brand.name,
        description=brand.description,
        keywords=brand.keywords or [],
        platforms=brand.platforms or [],
        status=brand.status.value,
        created_at=brand.created_at.isoformat(),
        updated_at=brand.updated_at.isoformat()
    )


@router.get("/brands", response_model=dict)
async def get_brands(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[BrandStatus] = None,
    db: Session = Depends(get_db)
):
    """获取品牌列表"""
    query = db.query(Brand)
    
    if status:
        query = query.filter(Brand.status == status)
    
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": [
                BrandResponse(
                    id=item.id,
                    name=item.name,
                    description=item.description,
                    keywords=item.keywords or [],
                    platforms=item.platforms or [],
                    status=item.status.value,
                    created_at=item.created_at.isoformat(),
                    updated_at=item.updated_at.isoformat()
                ).dict()
                for item in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


@router.get("/brands/{brand_id}", response_model=dict)
async def get_brand(brand_id: int, db: Session = Depends(get_db)):
    """获取品牌详情"""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="品牌不存在")
    
    return {
        "code": 200,
        "message": "success",
        "data": BrandResponse(
            id=brand.id,
            name=brand.name,
            description=brand.description,
            keywords=brand.keywords or [],
            platforms=brand.platforms or [],
            status=brand.status.value,
            created_at=brand.created_at.isoformat(),
            updated_at=brand.updated_at.isoformat()
        ).dict()
    }


@router.put("/brands/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: int,
    brand_data: BrandUpdate,
    db: Session = Depends(get_db)
):
    """更新品牌"""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="品牌不存在")
    
    # 更新字段
    if brand_data.name is not None:
        brand.name = brand_data.name
    if brand_data.description is not None:
        brand.description = brand_data.description
    if brand_data.keywords is not None:
        brand.keywords = brand_data.keywords
    if brand_data.platforms is not None:
        brand.platforms = brand_data.platforms
    if brand_data.status is not None:
        brand.status = brand_data.status
    
    db.commit()
    db.refresh(brand)
    
    return BrandResponse(
        id=brand.id,
        name=brand.name,
        description=brand.description,
        keywords=brand.keywords or [],
        platforms=brand.platforms or [],
        status=brand.status.value,
        created_at=brand.created_at.isoformat(),
        updated_at=brand.updated_at.isoformat()
    )


@router.delete("/brands/{brand_id}")
async def delete_brand(brand_id: int, db: Session = Depends(get_db)):
    """删除品牌"""
    from loguru import logger
    from fastapi import Response
    from app.models.crawl_task import CrawlTask
    from app.models.analysis_task import AnalysisTask
    from app.models.report import Report
    
    logger.info(f"开始删除品牌 ID={brand_id}")
    
    try:
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            logger.warning(f"品牌不存在 ID={brand_id}")
            raise HTTPException(status_code=404, detail="品牌不存在")
        
        brand_name = brand.name
        logger.info(f"找到品牌 ID={brand_id}, name={brand_name}")
        
        # 由于外键约束设置了CASCADE，理论上可以直接删除品牌
        # 但如果CASCADE没有正确设置，我们需要手动删除关联数据
        # 先尝试直接删除品牌，如果失败再手动删除关联数据
        
        # 手动删除关联数据（确保按正确顺序删除）
        # 使用 synchronize_session=False 避免参数绑定问题
        
        # 1. 先删除报告（reports可能引用analysis_tasks）
        try:
            report_count = db.query(Report).filter(Report.brand_id == brand_id).count()
            if report_count > 0:
                db.query(Report).filter(Report.brand_id == brand_id).delete(synchronize_session=False)
                logger.info(f"删除了 {report_count} 个报告")
        except Exception as e:
            logger.warning(f"删除报告时出错: {e}")
            # 继续执行，不中断
        
        # 2. 删除分析任务
        try:
            analysis_count = db.query(AnalysisTask).filter(AnalysisTask.brand_id == brand_id).count()
            if analysis_count > 0:
                db.query(AnalysisTask).filter(AnalysisTask.brand_id == brand_id).delete(synchronize_session=False)
                logger.info(f"删除了 {analysis_count} 个分析任务")
        except Exception as e:
            logger.warning(f"删除分析任务时出错: {e}")
            # 继续执行，不中断
        
        # 3. 删除爬虫任务
        try:
            crawl_count = db.query(CrawlTask).filter(CrawlTask.brand_id == brand_id).count()
            if crawl_count > 0:
                db.query(CrawlTask).filter(CrawlTask.brand_id == brand_id).delete(synchronize_session=False)
                logger.info(f"删除了 {crawl_count} 个爬虫任务")
        except Exception as e:
            logger.warning(f"删除爬虫任务时出错: {e}")
            # 继续执行，不中断
        
        # 4. 最后删除品牌
        db.delete(brand)
        db.commit()
        logger.info(f"成功删除品牌 ID={brand_id}, name={brand_name}")
        
        # 返回204 No Content
        return Response(status_code=204)
        
    except HTTPException:
        # 重新抛出HTTPException
        raise
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        logger.error(f"删除品牌失败 ID={brand_id}: {error_msg}", exc_info=True)
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"删除失败: {error_msg}")

