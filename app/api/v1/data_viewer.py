"""
数据查看API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List
from pathlib import Path
from loguru import logger

from app.core.database import get_mongodb, get_db
from app.models.brand import Brand
from sqlalchemy.orm import Session

router = APIRouter()

# 模板目录
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent.parent.parent / "templates"))


@router.get("/brands/{brand_id}/data/view", response_class=HTMLResponse)
async def view_brand_data_page(
    request: Request,
    brand_id: int,
    db: Session = Depends(get_db)
):
    """数据查看页面"""
    # 检查品牌是否存在
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="品牌不存在")
    
    return templates.TemplateResponse("data_viewer.html", {
        "request": request,
        "brand_id": brand_id,
        "brand_name": brand.name
    })


@router.get("/brands/{brand_id}/data", response_model=dict)
async def get_brand_data(
    brand_id: int,
    platform: Optional[str] = Query(None, description="平台筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取品牌爬取的数据"""
    # 检查品牌是否存在
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="品牌不存在")
    
    # 获取MongoDB数据
    try:
        mongodb = get_mongodb()
        
        # 构建查询条件
        query = {"brand_id": brand_id}
        if platform:
            query["platform"] = platform
        
        # 获取总数
        total = mongodb.raw_data.count_documents(query)
        
        # 分页查询
        skip = (page - 1) * page_size
        items = list(mongodb.raw_data.find(query)
                    .sort("crawled_at", -1)
                    .skip(skip)
                    .limit(page_size))
        
        # 转换ObjectId为字符串
        for item in items:
            item["_id"] = str(item["_id"])
            if "crawled_at" in item and hasattr(item["crawled_at"], "isoformat"):
                item["crawled_at"] = item["crawled_at"].isoformat()
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "brand_id": brand_id,
                "brand_name": brand.name,
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "platform": platform
            }
        }
    except Exception as e:
        logger.error(f"获取数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")


@router.get("/brands/{brand_id}/data/stats", response_model=dict)
async def get_brand_data_stats(
    brand_id: int,
    db: Session = Depends(get_db)
):
    """获取品牌数据统计"""
    # 检查品牌是否存在
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="品牌不存在")
    
    try:
        mongodb = get_mongodb()
        
        # 按平台统计
        pipeline = [
            {"$match": {"brand_id": brand_id}},
            {"$group": {
                "_id": "$platform",
                "count": {"$sum": 1},
                "latest_crawl": {"$max": "$crawled_at"}
            }},
            {"$sort": {"count": -1}}
        ]
        
        platform_stats = list(mongodb.raw_data.aggregate(pipeline))
        
        # 转换日期
        for stat in platform_stats:
            if "latest_crawl" in stat and hasattr(stat["latest_crawl"], "isoformat"):
                stat["latest_crawl"] = stat["latest_crawl"].isoformat()
        
        # 总数据量
        total = mongodb.raw_data.count_documents({"brand_id": brand_id})
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "brand_id": brand_id,
                "brand_name": brand.name,
                "total": total,
                "platforms": platform_stats
            }
        }
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")


@router.delete("/brands/{brand_id}/data", response_model=dict)
async def delete_brand_data(
    brand_id: int,
    platform: Optional[str] = Query(None, description="平台筛选，不指定则删除所有"),
    db: Session = Depends(get_db)
):
    """删除品牌数据"""
    # 检查品牌是否存在
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="品牌不存在")
    
    try:
        mongodb = get_mongodb()
        
        # 构建查询条件
        query = {"brand_id": brand_id}
        if platform:
            query["platform"] = platform
        
        # 删除数据
        result = mongodb.raw_data.delete_many(query)
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "brand_id": brand_id,
                "deleted_count": result.deleted_count,
                "platform": platform or "all"
            }
        }
    except Exception as e:
        logger.error(f"删除数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除数据失败: {str(e)}")




