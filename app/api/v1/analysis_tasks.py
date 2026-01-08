"""
数据分析API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from pathlib import Path

from app.core.database import get_db
from app.models.brand import Brand
from app.models.analysis_task import AnalysisTask
from app.models.crawl_task import TaskStatus

router = APIRouter()

# 初始化模板引擎
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent.parent.parent / "templates"))


# 请求模型
class AnalysisTaskCreate(BaseModel):
    analysis_type: str = "full"
    include_sentiment: bool = True
    include_topics: bool = True
    include_keywords: bool = True
    include_insights: bool = True


@router.get("/analysis/recent", response_model=dict)
async def get_recent_analysis_tasks(limit: int = 5, db: Session = Depends(get_db)):
    """获取最近完成的分析任务"""
    tasks = db.query(AnalysisTask).filter(
        AnalysisTask.status == TaskStatus.COMPLETED
    ).order_by(AnalysisTask.completed_at.desc()).limit(limit).all()
    
    result = []
    for task in tasks:
        brand = db.query(Brand).filter(Brand.id == task.brand_id).first()
        if brand:
            result.append({
                "task_id": task.id,
                "brand_id": brand.id,
                "brand_name": brand.name,
                "analysis_type": task.analysis_type,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            })
            
    return {
        "code": 200,
        "message": "success",
        "data": result
    }


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


@router.get("/brands/{brand_id}/analysis")
async def get_analysis(brand_id: int, include_charts: bool = True, db: Session = Depends(get_db)):
    """获取分析结果"""
    from loguru import logger
    
    try:
        # 检查品牌是否存在
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            logger.warning(f"品牌不存在: {brand_id}")
            return JSONResponse(
                status_code=200,  # 始终返回200，用code字段表示业务状态
                content={
                    "code": 404,
                    "message": "品牌不存在",
                    "data": {
                        "brand_id": brand_id,
                        "error": "品牌不存在，请检查品牌ID是否正确"
                    }
                }
            )
        
        # 获取最新的分析任务（包括进行中的任务）
        task = db.query(AnalysisTask).filter(
            AnalysisTask.brand_id == brand_id,
            AnalysisTask.status == TaskStatus.COMPLETED
        ).order_by(AnalysisTask.completed_at.desc()).first()
        
        # 如果没有完成的任务，检查是否有进行中的任务
        if not task:
            pending_task = db.query(AnalysisTask).filter(
                AnalysisTask.brand_id == brand_id,
                AnalysisTask.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING])
            ).order_by(AnalysisTask.created_at.desc()).first()
            
            if pending_task:
                logger.info(f"品牌 {brand_id} 有进行中的分析任务: {pending_task.id}")
                return JSONResponse(
                    status_code=200,
                    content={
                        "code": 202,
                        "message": "分析任务进行中",
                        "data": {
                            "brand_id": brand_id,
                            "brand_name": brand.name,
                            "task_id": pending_task.id,
                            "status": pending_task.status.value,
                            "progress": pending_task.progress,
                            "message": "分析任务正在进行中，请稍后再试"
                        }
                    }
                )
            else:
                logger.info(f"品牌 {brand_id} 没有分析任务")
                return JSONResponse(
                    status_code=200,
                    content={
                        "code": 404,
                        "message": "暂无分析结果",
                        "data": {
                            "brand_id": brand_id,
                            "brand_name": brand.name,
                            "message": "该品牌还没有完成分析任务，请先启动分析"
                        }
                    }
                )
        
        # 从MongoDB获取详细分析结果
        try:
            from app.core.database import get_mongodb
            mongodb = get_mongodb()
            result = mongodb.analysis_results.find_one({"analysis_task_id": task.id})
            
            if result:
                analysis_result = result.get("result", {})
                
                # 如果需要图表，生成图表数据
                charts = {}
                if include_charts:
                    try:
                        from app.services.report_service import report_service
                        charts = report_service.generate_charts(analysis_result)
                    except Exception as e:
                        logger.error(f"生成图表失败: {e}", exc_info=True)
                        charts = {}  # 即使图表生成失败，也返回其他数据
                
                return JSONResponse(
                    status_code=200,
                    content={
                        "code": 200,
                        "message": "success",
                        "data": {
                            "brand_id": brand_id,
                            "brand_name": brand.name,
                            "analysis_task_id": task.id,
                            "generated_at": task.completed_at.isoformat() if task.completed_at else None,
                            "result": analysis_result,
                            "charts": charts
                        }
                    }
                )
            else:
                logger.warning(f"分析任务 {task.id} 在MongoDB中未找到结果")
                return JSONResponse(
                    status_code=200,
                    content={
                        "code": 404,
                        "message": "分析结果未找到",
                        "data": {
                            "brand_id": brand_id,
                            "brand_name": brand.name,
                            "analysis_task_id": task.id,
                            "generated_at": task.completed_at.isoformat() if task.completed_at else None,
                            "message": "分析任务已完成，但结果数据未找到，可能数据存储出现问题"
                        }
                    }
                )
        except Exception as e:
            logger.error(f"获取分析结果失败: {e}", exc_info=True)
            return JSONResponse(
                status_code=200,
                content={
                    "code": 500,
                    "message": "服务器错误",
                    "data": {
                        "brand_id": brand_id,
                        "brand_name": brand.name if brand else None,
                        "analysis_task_id": task.id if task else None,
                        "error": str(e),
                        "message": f"获取分析结果时发生错误: {str(e)}"
                    }
                }
            )
    except Exception as e:
        logger.error(f"获取分析结果时发生未预期的错误: {e}", exc_info=True)
        return JSONResponse(
            status_code=200,
            content={
                "code": 500,
                "message": "服务器错误",
                "data": {
                    "brand_id": brand_id,
                    "error": str(e),
                    "message": f"获取分析结果时发生错误: {str(e)}"
                }
            }
        )


@router.get("/brands/{brand_id}/analysis/preview", response_model=dict)
async def get_analysis_preview(brand_id: int, db: Session = Depends(get_db)):
    """获取分析结果预览（HTML格式，用于页面展示）"""
    from fastapi.responses import HTMLResponse
    from app.core.database import get_mongodb
    from app.services.report_service import report_service
    
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
    mongodb = get_mongodb()
    result = mongodb.analysis_results.find_one({"analysis_task_id": task.id})
    
    if not result:
        raise HTTPException(status_code=404, detail="分析结果不存在")
    
    analysis_result = result.get("result", {})
    
    # 准备报表数据
    brand_info = {
        "id": brand.id,
        "name": brand.name,
        "description": brand.description
    }
    
    report_data = report_service.prepare_report_data(
        brand_name=brand.name,
        analysis_result=analysis_result,
        brand_info=brand_info
    )
    
    # 生成图表
    charts = report_service.generate_charts(analysis_result)
    
    # 渲染HTML报表
    html_content = report_service.render_html_report(
        report_data=report_data,
        charts=charts,
        template_name="brand_report.html"
    )
    
    return HTMLResponse(content=html_content)


@router.get("/brands/{brand_id}/analysis/view")
async def view_brand_analysis(
    brand_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """查看品牌分析报告页面"""
    # 检查品牌是否存在
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="品牌不存在")
    
    return templates.TemplateResponse(
        "brand_analysis.html",
        {
            "request": request,
            "brand_id": brand_id,
            "brand_name": brand.name
        }
    )

