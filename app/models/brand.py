"""
品牌模型
"""
from sqlalchemy import Column, Integer, String, Text, JSON, Enum, DateTime
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class BrandStatus(str, enum.Enum):
    """品牌状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class Brand(Base):
    """品牌表"""
    __tablename__ = "brands"
    
    id = Column(Integer, primary_key=True, index=True, comment="品牌ID")
    name = Column(String(100), nullable=False, index=True, comment="品牌名称")
    description = Column(Text, comment="品牌描述")
    keywords = Column(JSON, comment="关键词列表")
    platforms = Column(JSON, comment="支持的平台列表")
    status = Column(
        Enum(BrandStatus),
        default=BrandStatus.ACTIVE,
        index=True,
        comment="状态"
    )
    created_at = Column(
        DateTime,
        server_default=func.now(),
        comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )
    
    def __repr__(self):
        return f"<Brand(id={self.id}, name='{self.name}')>"

