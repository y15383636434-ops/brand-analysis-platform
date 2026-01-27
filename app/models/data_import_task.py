"""
数据导入任务模型
"""
from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base
from app.models.crawl_task import TaskStatus


class DataImportTask(Base):
    """数据导入任务表"""
    __tablename__ = "data_import_tasks"
    
    id = Column(Integer, primary_key=True, index=True, comment="任务ID")
    brand_id = Column(
        Integer,
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="品牌ID"
    )
    celery_task_id = Column(String(50), index=True, comment="Celery任务ID")
    status = Column(
        Enum(TaskStatus),
        default=TaskStatus.PENDING,
        index=True,
        comment="任务状态"
    )
    file_list = Column(JSON, comment="文件列表")
    total_files = Column(Integer, default=0, comment="总文件数")
    processed_files = Column(Integer, default=0, comment="已处理文件数")
    imported_items = Column(Integer, default=0, comment="导入数据条数")
    skipped_items = Column(Integer, default=0, comment="跳过数据条数")
    error_message = Column(Text, comment="错误信息")
    
    created_at = Column(DateTime, server_default=func.now(), index=True, comment="创建时间")
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    
    # 关系
    brand = relationship("Brand", backref="import_tasks")
    
    def __repr__(self):
        return f"<DataImportTask(id={self.id}, brand_id={self.brand_id}, status='{self.status}')>"
