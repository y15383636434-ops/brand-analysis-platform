"""
分析任务模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Enum, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base
from app.models.crawl_task import TaskStatus


class AnalysisTask(Base):
    """分析任务表"""
    __tablename__ = "analysis_tasks"
    
    id = Column(Integer, primary_key=True, index=True, comment="任务ID")
    brand_id = Column(
        Integer,
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="品牌ID"
    )
    status = Column(
        Enum(TaskStatus),
        default=TaskStatus.PENDING,
        index=True,
        comment="任务状态"
    )
    analysis_type = Column(String(50), default="full", comment="分析类型")
    include_sentiment = Column(Boolean, default=True, comment="包含情感分析")
    include_topics = Column(Boolean, default=True, comment="包含主题提取")
    include_keywords = Column(Boolean, default=True, comment="包含关键词分析")
    include_insights = Column(Boolean, default=True, comment="包含深度洞察")
    celery_task_id = Column(String(255), comment="Celery任务ID")
    progress = Column(Integer, default=0, comment="进度百分比 0-100")
    error_message = Column(Text, comment="错误信息")
    created_at = Column(DateTime, server_default=func.now(), index=True, comment="创建时间")
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    duration = Column(Integer, comment="耗时（秒）")
    
    # 关系
    brand = relationship("Brand", backref="analysis_tasks")
    
    def __repr__(self):
        return f"<AnalysisTask(id={self.id}, brand_id={self.brand_id}, status='{self.status}')>"

