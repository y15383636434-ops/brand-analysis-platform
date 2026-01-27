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
        
        # 构建查询条件（兼容历史数据：brand_id 可能被存成 str）
        query = {"brand_id": {"$in": [brand_id, str(brand_id)]}}
        if platform:
            query["platform"] = platform
            
        logger.info(f"查询品牌数据: brand_id={brand_id}, query={query}")
        
        # 获取总数
        total = mongodb.raw_data.count_documents(query)
        logger.info(f"查询到数据总数: {total}")
        
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
        
        # 调试：检查raw_data集合中是否有任何数据
        any_doc = mongodb.raw_data.find_one()
        if any_doc:
            logger.info(f"MongoDB raw_data 集合首条数据示例: {any_doc.get('_id')}, brand_id字段存在: {'brand_id' in any_doc}, brand_id类型: {type(any_doc.get('brand_id'))}")
        else:
            logger.info("MongoDB raw_data 集合为空")

        # 检查所有存在的brand_id
        distinct_brands = mongodb.raw_data.distinct("brand_id")
        logger.info(f"MongoDB中存在的品牌ID列表: {distinct_brands}, 当前查询ID: {brand_id} (类型: {type(brand_id)})")

        # 按平台统计（兼容 brand_id 类型）
        pipeline = [
            {"$match": {"brand_id": {"$in": [brand_id, str(brand_id)]}}},
            {"$group": {
                "_id": "$platform",
                "count": {"$sum": 1},
                "latest_crawl": {"$max": "$crawled_at"}
            }},
            {"$sort": {"count": -1}}
        ]
        
        logger.info(f"执行统计聚合查询: brand_id={brand_id}")
        platform_stats = list(mongodb.raw_data.aggregate(pipeline))
        logger.info(f"统计结果: {platform_stats}")
        
        # 转换日期
        for stat in platform_stats:
            if "latest_crawl" in stat and hasattr(stat["latest_crawl"], "isoformat"):
                stat["latest_crawl"] = stat["latest_crawl"].isoformat()
        
        # 总数据量
        total = mongodb.raw_data.count_documents({"brand_id": {"$in": [brand_id, str(brand_id)]}})
        
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


from pydantic import BaseModel

class DeleteDataRequest(BaseModel):
    ids: List[str]

@router.post("/brands/{brand_id}/data/delete-batch", response_model=dict)
async def delete_brand_data_batch(
    brand_id: int,
    request: DeleteDataRequest,
    db: Session = Depends(get_db)
):
    """批量删除品牌数据"""
    # 检查品牌是否存在
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="品牌不存在")
    
    try:
        if not request.ids:
            return {
                "code": 200,
                "message": "未选择任何数据",
                "data": {"deleted_count": 0}
            }
            
        mongodb = get_mongodb()
        
        # 转换ID字符串为ObjectId (如果存储的是ObjectId)
        # raw_data中通常使用content_id作为唯一标识，或者直接使用MongoDB生成的_id
        # 这里假设前端传回的是MongoDB的_id字符串
        from bson.objectid import ObjectId
        object_ids = []
        for id_str in request.ids:
            try:
                object_ids.append(ObjectId(id_str))
            except:
                # 如果不是有效的ObjectId，可能是自定义ID，尝试作为content_id删除?
                # 暂时只支持_id删除，因为get_brand_data返回的是_id
                pass
        
        if not object_ids:
             # 如果没有转换成功的ObjectId，尝试匹配字符串类型的_id (兼容某些特殊情况)
             # 或者匹配content_id? 
             # 现在的逻辑是前端拿到的item["_id"]是str(ObjectId)，所以应该能转换回去
             pass

        # 删除数据
        result = mongodb.raw_data.delete_many({
            "brand_id": brand_id,
            "_id": {"$in": object_ids}
        })
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "brand_id": brand_id,
                "deleted_count": result.deleted_count
            }
        }
    except Exception as e:
        logger.error(f"批量删除数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量删除数据失败: {str(e)}")


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
