"""
报告生成API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from pathlib import Path
import tempfile
import os
from datetime import datetime

from app.core.database import get_db
from app.models.brand import Brand
from app.models.report import Report, ReportStatus
from app.models.analysis_task import AnalysisTask
from app.models.crawl_task import TaskStatus
from config import settings

router = APIRouter()


# 请求模型
class ReportCreate(BaseModel):
    report_type: str = "full"
    format: str = "pdf"
    include_charts: bool = True
    language: str = "zh-CN"


@router.get("/brands/{brand_id}/reports")
async def export_brand_report(
    brand_id: int,
    format: str = Query("pdf", regex="^(pdf|md|markdown)$"),
    db: Session = Depends(get_db)
):
    """
    即时导出最新分析报告 (支持 PDF 和 Markdown)
    """
    # 检查品牌是否存在
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="品牌不存在")
    
    # 获取最新的已完成分析任务
    task = db.query(AnalysisTask).filter(
        AnalysisTask.brand_id == brand_id,
        AnalysisTask.status == TaskStatus.COMPLETED
    ).order_by(AnalysisTask.completed_at.desc()).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="该品牌暂无已完成的分析任务，无法生成报告")
    
    # 从MongoDB获取详细分析结果
    from app.core.database import get_mongodb
    mongodb = get_mongodb()
    result = mongodb.analysis_results.find_one({"analysis_task_id": task.id})
    
    if not result:
        raise HTTPException(status_code=404, detail="分析结果数据丢失")
        
    analysis_result = result.get("result", {})
    
    # 准备报表数据
    from app.services.report_service import report_service
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
    
    # 根据格式生成报告
    if format in ["md", "markdown"]:
        # 生成 Markdown
        md_content = report_service.generate_markdown_report(report_data)
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp:
            tmp.write(md_content)
            tmp_path = tmp.name
            
        filename = f"{brand.name}_分析报告_{datetime.now().strftime('%Y%m%d')}.md"
        
        # 返回文件，并在发送后删除（需配合后台任务删除，这里简单处理由FileResponse管理读取，但不自动删除）
        # 为了自动删除，可以使用 BackgroundTask
        from starlette.background import BackgroundTask
        
        def cleanup(path):
            try:
                os.remove(path)
            except Exception:
                pass
                
        return FileResponse(
            tmp_path,
            filename=filename,
            media_type="text/markdown",
            background=BackgroundTask(cleanup, tmp_path)
        )
        
    else:
        # 生成 PDF (现有的逻辑，可能需要异步，这里暂时报错提示使用POST接口如果太慢)
        # 为了简单起见，这里复用 HTML -> PDF 逻辑
        charts = report_service.generate_charts(analysis_result)
        html_content = report_service.render_html_report(
            report_data=report_data,
            charts=charts
        )
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name
            
        success = report_service.html_to_pdf(html_content, Path(tmp_path))
        
        if not success:
            raise HTTPException(status_code=500, detail="PDF生成失败，请检查服务器配置或尝试Markdown格式")
            
        filename = f"{brand.name}_分析报告_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        from starlette.background import BackgroundTask
        def cleanup(path):
            try:
                os.remove(path)
            except Exception:
                pass
                
        return FileResponse(
            tmp_path,
            filename=filename,
            media_type="application/pdf",
            background=BackgroundTask(cleanup, tmp_path)
        )


@router.post("/brands/{brand_id}/reports", response_model=dict)
async def generate_report(
    brand_id: int,
    report_data: ReportCreate,
    db: Session = Depends(get_db)
):
    """生成报告"""
    # 检查品牌是否存在
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="品牌不存在")
    
    # 创建报告记录
    report = Report(
        brand_id=brand_id,
        report_type=report_data.report_type,
        format=report_data.format,
        language=report_data.language,
        status=ReportStatus.GENERATING
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    # 异步生成报告（使用Celery）
    from app.tasks.report_tasks import generate_report_task
    generate_report_task.delay(report.id)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "report_id": report.id,
            "brand_id": brand_id,
            "report_type": report_data.report_type,
            "format": report_data.format,
            "status": "generating"
        }
    }


@router.get("/reports", response_model=dict)
async def get_reports(
    brand_id: int = None,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    """获取报告列表"""
    query = db.query(Report)
    
    if brand_id:
        query = query.filter(Report.brand_id == brand_id)
    
    total = query.count()
    items = query.order_by(Report.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": [
                {
                    "id": item.id,
                    "brand_id": item.brand_id,
                    "report_type": item.report_type,
                    "format": item.format,
                    "file_size": item.file_size,
                    "status": item.status.value,
                    "created_at": item.created_at.isoformat(),
                    "download_url": f"/api/v1/reports/{item.id}/download" if item.status == ReportStatus.COMPLETED else None
                }
                for item in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


@router.get("/reports/{report_id}/download")
async def download_report(report_id: int, db: Session = Depends(get_db)):
    """下载报告"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    if report.status != ReportStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="报告尚未生成完成")
    
    if not report.file_path or not Path(report.file_path).exists():
        raise HTTPException(status_code=404, detail="报告文件不存在")
    
    return FileResponse(
        report.file_path,
        filename=f"brand_report_{report.brand_id}_{report.id}.{report.format}",
        media_type="application/pdf" if report.format == "pdf" else "application/octet-stream"
    )

