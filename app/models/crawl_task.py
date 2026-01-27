"""
爬虫任务模型
"""
from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class TaskStatus(str, enum.Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CrawlType(str, enum.Enum):
    """爬取类型"""
    SEARCH = "search"       # 关键词搜索
    CREATOR = "creator"     # 指定博主
    DETAIL = "detail"       # 指定帖子/视频


class CrawlTask(Base):
    """爬虫任务表"""
    __tablename__ = "crawl_tasks"
    
    id = Column(Integer, primary_key=True, index=True, comment="任务ID")
    brand_id = Column(
        Integer,
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="品牌ID"
    )
    platform = Column(String(50), nullable=False, index=True, comment="平台名称")
    crawl_type = Column(
        Enum(CrawlType),
        default=CrawlType.SEARCH,
        comment="爬取类型"
    )
    status = Column(
        Enum(TaskStatus),
        default=TaskStatus.PENDING,
        index=True,
        comment="任务状态"
    )
    keyword = Column(String(200), comment="搜索关键词")
    target_url = Column(Text, comment="目标链接(博主主页/帖子链接)")
    max_items = Column(Integer, default=100, comment="最大采集数量")
    total_items = Column(Integer, default=0, comment="总数据量")
    crawled_items = Column(Integer, default=0, comment="已采集数量")
    failed_items = Column(Integer, default=0, comment="失败数量")
    progress = Column(Integer, default=0, comment="进度百分比 0-100")
    error_message = Column(Text, comment="错误信息")
    download_media = Column(Integer, default=1, comment="是否下载媒体 1是0否")
    created_at = Column(DateTime, server_default=func.now(), index=True, comment="创建时间")
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    duration = Column(Integer, comment="耗时（秒）")
    
    # 关系
    brand = relationship("Brand", backref="crawl_tasks")
    
    def __repr__(self):
        return f"<CrawlTask(id={self.id}, brand_id={self.brand_id}, platform='{self.platform}', type='{self.crawl_type}', status='{self.status}')>"
