"""
数据库初始化脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from config import settings
from loguru import logger

def init_database():
    """初始化数据库"""
    logger.info("开始初始化数据库...")
    
    # 创建数据库（如果不存在）
    mysql_url = (
        f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
        f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}"
        f"?charset=utf8mb4"
    )
    
    engine = create_engine(mysql_url)
    
    try:
        with engine.connect() as conn:
            # 创建数据库
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {settings.MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            conn.commit()
        logger.info(f"数据库 {settings.MYSQL_DATABASE} 创建成功")
    except Exception as e:
        logger.error(f"创建数据库失败: {e}")
        return
    
    # 创建表
    from app.core.database import engine, Base
    from app.models import Brand, CrawlTask, AnalysisTask, Report, DataImportTask
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"创建表失败: {e}")
        return
    
    logger.info("数据库初始化完成！")


if __name__ == "__main__":
    init_database()

