"""
报告生成API
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from pathlib import Path

from app.core.database import get_db
from app.models.brand import Brand
from app.models.report import Report, ReportStatus
from config import settings

router = APIRouter()


# 请求模型
class ReportCreate(BaseModel):
    report_type: str = "full"
    format: str = "pdf"
    include_charts: bool = True
    language: str = "zh-CN"


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
    
    # TODO: 这里应该异步生成报告（使用Celery）
    # from app.tasks.report import generate_report_task
    # generate_report_task.delay(report.id)
    
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

