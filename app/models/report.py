"""
报告模型
"""
from sqlalchemy import Column, Integer, String, Text, BigInteger, Enum, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base
from app.models.crawl_task import TaskStatus


class ReportStatus(str, enum.Enum):
    """报告状态"""
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Report(Base):
    """报告表"""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True, comment="报告ID")
    brand_id = Column(
        Integer,
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="品牌ID"
    )
    analysis_task_id = Column(
        Integer,
        ForeignKey("analysis_tasks.id", ondelete="SET NULL"),
        index=True,
        comment="关联的分析任务ID"
    )
    report_type = Column(String(50), default="full", comment="报告类型")
    format = Column(String(20), default="pdf", comment="文件格式")
    file_path = Column(String(500), comment="文件路径")
    file_size = Column(BigInteger, comment="文件大小（字节）")
    file_url = Column(String(500), comment="文件访问URL")
    language = Column(String(10), default="zh-CN", comment="语言")
    status = Column(
        Enum(ReportStatus),
        default=ReportStatus.GENERATING,
        index=True,
        comment="状态"
    )
    error_message = Column(Text, comment="错误信息")
    created_at = Column(DateTime, server_default=func.now(), index=True, comment="创建时间")
    completed_at = Column(DateTime, comment="完成时间")
    
    # 关系
    brand = relationship("Brand", backref="reports")
    analysis_task = relationship("AnalysisTask", backref="reports")
    
    def __repr__(self):
        return f"<Report(id={self.id}, brand_id={self.brand_id}, format='{self.format}', status='{self.status}')>"

