from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from fastapi import HTTPException
from loguru import logger

from app.models.brand import Brand, BrandStatus
from app.models.report import Report
from app.models.analysis_task import AnalysisTask
from app.models.crawl_task import CrawlTask


class BrandService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, name: str) -> Optional[Brand]:
        """通过名称获取品牌"""
        result = await self.db.execute(select(Brand).where(Brand.name == name))
        return result.scalars().first()

    async def create(self, name: str, description: str = "", keywords: List[str] = None, platforms: List[str] = None) -> Brand:
        """创建品牌"""
        # 检查是否存在
        existing = await self.get_by_name(name)
        if existing:
            return existing
            
        brand = Brand(
            name=name,
            description=description,
            keywords=keywords or [name],
            platforms=platforms or ["xhs", "douyin", "weibo", "zhihu"]
        )
        self.db.add(brand)
        await self.db.commit()
        await self.db.refresh(brand)
        return brand

    async def get(self, brand_id: int) -> Optional[Brand]:
        """获取品牌详情"""
        result = await self.db.execute(select(Brand).where(Brand.id == brand_id))
        return result.scalars().first()

    async def get_list(self, page: int = 1, page_size: int = 10, status: Optional[BrandStatus] = None) -> Tuple[List[Brand], int]:
        """获取品牌列表"""
        query = select(Brand)
        if status:
            query = query.where(Brand.status == status)
            
        # 计算总数
        # 注意: select(func.count()).select_from(query.subquery()) 这种写法兼容性更好
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 分页获取
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        return items, total

    async def update(self, brand_id: int, **kwargs) -> Optional[Brand]:
        """更新品牌"""
        brand = await self.get(brand_id)
        if not brand:
            return None
            
        for key, value in kwargs.items():
            if value is not None and hasattr(brand, key):
                setattr(brand, key, value)
                
        await self.db.commit()
        await self.db.refresh(brand)
        return brand

    async def delete(self, brand_id: int) -> bool:
        """删除品牌（级联删除）"""
        brand = await self.get(brand_id)
        if not brand:
            return False
            
        # 手动级联删除
        try:
            # 1. 删除报告
            await self.db.execute(delete(Report).where(Report.brand_id == brand_id))
            
            # 2. 删除分析任务
            await self.db.execute(delete(AnalysisTask).where(AnalysisTask.brand_id == brand_id))
            
            # 3. 删除爬虫任务
            await self.db.execute(delete(CrawlTask).where(CrawlTask.brand_id == brand_id))
            
            # 4. 删除品牌
            await self.db.delete(brand)
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"删除品牌失败 ID={brand_id}: {e}")
            raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
