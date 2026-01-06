"""
数据分析API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.brand import Brand
from app.models.analysis_task import AnalysisTask
from app.models.crawl_task import TaskStatus

router = APIRouter()


# 请求模型
class AnalysisTaskCreate(BaseModel):
    analysis_type: str = "full"
    include_sentiment: bool = True
    include_topics: bool = True
    include_keywords: bool = True
    include_insights: bool = True


@router.post("/brands/{brand_id}/analyze", response_model=dict)
async def start_analysis(
    brand_id: int,
    task_data: AnalysisTaskCreate,
    db: Session = Depends(get_db)
):
    """启动分析任务"""
    # 检查品牌是否存在
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="品牌不存在")
    
    # 创建分析任务
    task = AnalysisTask(
        brand_id=brand_id,
        analysis_type=task_data.analysis_type,
        include_sentiment=task_data.include_sentiment,
        include_topics=task_data.include_topics,
        include_keywords=task_data.include_keywords,
        include_insights=task_data.include_insights,
        status=TaskStatus.PENDING
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # 异步启动分析任务（使用Celery）
    from app.tasks.analysis_tasks import analyze_brand_task
    analyze_brand_task.delay(task.id)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "task_id": task.id,
            "brand_id": brand_id,
            "analysis_type": task_data.analysis_type,
            "status": "pending"
        }
    }


@router.get("/brands/{brand_id}/analysis", response_model=dict)
async def get_analysis(brand_id: int, db: Session = Depends(get_db)):
    """获取分析结果"""
    # 检查品牌是否存在
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="品牌不存在")
    
    # 获取最新的分析任务
    task = db.query(AnalysisTask).filter(
        AnalysisTask.brand_id == brand_id,
        AnalysisTask.status == TaskStatus.COMPLETED
    ).order_by(AnalysisTask.completed_at.desc()).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="暂无分析结果")
    
    # 从MongoDB获取详细分析结果
    try:
        from app.core.database import get_mongodb
        mongodb = get_mongodb()
        result = mongodb.analysis_results.find_one({"analysis_task_id": task.id})
        
        if result:
            return {
                "code": 200,
                "message": "success",
                "data": {
                    "brand_id": brand_id,
                    "analysis_task_id": task.id,
                    "generated_at": task.completed_at.isoformat() if task.completed_at else None,
                    "result": result.get("result", {})
                }
            }
        else:
            return {
                "code": 200,
                "message": "success",
                "data": {
                    "brand_id": brand_id,
                    "analysis_task_id": task.id,
                    "generated_at": task.completed_at.isoformat() if task.completed_at else None,
                    "message": "分析结果未找到"
                }
            }
    except Exception as e:
        return {
            "code": 200,
            "message": "success",
            "data": {
                "brand_id": brand_id,
                "analysis_task_id": task.id,
                "generated_at": task.completed_at.isoformat() if task.completed_at else None,
                "error": str(e)
            }
        }

