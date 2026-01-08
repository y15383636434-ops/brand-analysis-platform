"""
报表生成Celery任务
"""
from celery import Task
from loguru import logger
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime

from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal, get_mongodb
from app.models.report import Report, ReportStatus
from app.models.brand import Brand
from app.models.analysis_task import AnalysisTask
from app.models.crawl_task import TaskStatus
from app.services.report_service import report_service
from config import settings


@celery_app.task(bind=True, name="generate_report_task")
def generate_report_task(self: Task, report_id: int):
    """
    生成报表任务
    
    Args:
        report_id: 报表ID
    """
    db: Session = SessionLocal()
    
    try:
        # 获取报表记录
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            logger.error(f"报表不存在: {report_id}")
            return {"error": "报表不存在"}
        
        # 更新任务状态为生成中
        report.status = ReportStatus.GENERATING
        report.celery_task_id = self.request.id
        db.commit()
        
        logger.info(f"开始生成报表: {report_id}, 品牌ID: {report.brand_id}")
        
        # 获取品牌信息
        brand = db.query(Brand).filter(Brand.id == report.brand_id).first()
        if not brand:
            report.status = ReportStatus.FAILED
            report.error_message = "品牌不存在"
            db.commit()
            return {"error": "品牌不存在"}
        
        # 获取最新的分析结果
        analysis_task = db.query(AnalysisTask).filter(
            AnalysisTask.brand_id == report.brand_id,
            AnalysisTask.status == TaskStatus.COMPLETED
        ).order_by(AnalysisTask.completed_at.desc()).first()
        
        if not analysis_task:
            report.status = ReportStatus.FAILED
            report.error_message = "没有可用的分析结果"
            db.commit()
            return {"error": "没有可用的分析结果"}
        
        # 从MongoDB获取分析结果
        mongodb = get_mongodb()
        analysis_result_doc = mongodb.analysis_results.find_one({
            "analysis_task_id": analysis_task.id
        })
        
        if not analysis_result_doc:
            report.status = ReportStatus.FAILED
            report.error_message = "分析结果不存在"
            db.commit()
            return {"error": "分析结果不存在"}
        
        analysis_result = analysis_result_doc.get("result", {})
        
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
        logger.info("生成图表...")
        charts = report_service.generate_charts(analysis_result)
        
        # 渲染HTML报表
        logger.info("渲染HTML报表...")
        html_content = report_service.render_html_report(
            report_data=report_data,
            charts=charts,
            template_name="brand_report.html"
        )
        
        # 保存HTML报表
        html_filename = f"report_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        html_path = report_service.save_html_report(html_content, html_filename)
        
        # 根据格式生成文件
        if report.format == "pdf":
            logger.info("生成PDF报表...")
            pdf_filename = f"report_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = settings.REPORT_OUTPUT_DIR / pdf_filename
            
            success = report_service.html_to_pdf(html_content, pdf_path)
            
            if success:
                report.file_path = str(pdf_path)
                report.file_size = pdf_path.stat().st_size if pdf_path.exists() else 0
            else:
                # 如果PDF生成失败，使用HTML文件
                logger.warning("PDF生成失败，使用HTML文件")
                report.file_path = str(html_path)
                report.file_size = html_path.stat().st_size if html_path.exists() else 0
                report.format = "html"  # 更新格式为HTML
        else:
            # HTML格式
            report.file_path = str(html_path)
            report.file_size = html_path.stat().st_size if html_path.exists() else 0
        
        # 更新报表状态为完成
        report.status = ReportStatus.COMPLETED
        report.completed_at = datetime.now()
        report.analysis_task_id = analysis_task.id
        db.commit()
        
        logger.info(f"报表生成完成: {report_id}, 文件: {report.file_path}")
        
        return {
            "report_id": report_id,
            "status": "completed",
            "file_path": report.file_path,
            "file_size": report.file_size,
            "format": report.format
        }
        
    except Exception as e:
        logger.error(f"报表生成失败: {e}", exc_info=True)
        
        # 更新报表状态为失败
        if report:
            report.status = ReportStatus.FAILED
            report.error_message = str(e)
            db.commit()
        
        return {"error": str(e)}
    
    finally:
        db.close()


