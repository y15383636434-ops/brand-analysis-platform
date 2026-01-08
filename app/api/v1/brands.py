"""
品牌管理API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_async_db
from app.models.brand import BrandStatus
from app.services.brand_service import BrandService
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
    created_at: str
    updated_at: str
    
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
