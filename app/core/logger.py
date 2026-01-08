import sys
from pathlib import Path
from loguru import logger
from config import settings

def setup_logging():
    """配置日志"""
    # 移除默认handler
    logger.remove()
    
    # 控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True
    )
    
    # 文件输出
    logger.add(
        settings.LOG_FILE,
        rotation="10 MB",
        retention="7 days",
        level=settings.LOG_LEVEL,
        encoding='utf-8',
        errors='replace',
        enqueue=True  # 异步写入，线程安全
    )
    
    return logger
