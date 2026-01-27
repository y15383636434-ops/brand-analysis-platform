"""
数据模型
"""
from app.models.brand import Brand
from app.models.crawl_task import CrawlTask
from app.models.analysis_task import AnalysisTask
from app.models.report import Report
from app.models.data_import_task import DataImportTask

__all__ = ["Brand", "CrawlTask", "AnalysisTask", "Report", "DataImportTask"]
