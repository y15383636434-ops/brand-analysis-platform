"""
数据库连接和初始化
"""
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from pymongo import MongoClient
from redis import Redis
from loguru import logger

from config import settings

# MySQL数据库 (同步 - 用于Celery和旧代码)
SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
    f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
    f"?charset=utf8mb4"
)

# 使用 QueuePool 替代 NullPool 以提高性能，除非有明确理由不用
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# MySQL数据库 (异步 - 用于FastAPI接口)
SQLALCHEMY_ASYNC_DATABASE_URL = (
    f"mysql+aiomysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
    f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
    f"?charset=utf8mb4"
)

async_engine = create_async_engine(
    SQLALCHEMY_ASYNC_DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG,
    pool_size=20,     # 增加异步池大小
    max_overflow=20
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# MongoDB数据库（可选，连接失败不影响应用启动）
mongo_client = None
mongodb = None
try:
    mongo_client = MongoClient(
        host=settings.MONGODB_HOST,
        port=settings.MONGODB_PORT,
        serverSelectionTimeoutMS=2000  # 2秒超时
    )
    mongodb = mongo_client[settings.MONGODB_DATABASE]
except Exception as e:
    logger.warning(f"MongoDB连接失败（可选服务）: {e}")

# Redis连接（可选，连接失败不影响应用启动）
redis_client = None
try:
    redis_client = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=2  # 2秒超时
    )
    redis_client.ping()  # 测试连接
except Exception as e:
    logger.warning(f"Redis连接失败（可选服务）: {e}")
    redis_client = None


async def init_db():
    """初始化数据库"""
    # 测试MySQL同步连接
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("MySQL同步连接成功")
    except Exception as e:
        logger.error(f"MySQL同步连接失败（必需服务）: {e}")
        raise

    # 测试MySQL异步连接
    try:
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("MySQL异步连接成功")
    except Exception as e:
        logger.error(f"MySQL异步连接失败: {e}")
        # 异步连接失败暂时不阻断启动，因为可能只是配置问题

    # 测试MongoDB连接（可选）
    if mongo_client:
        try:
            mongo_client.admin.command('ping')
            logger.info("MongoDB连接成功")
        except Exception as e:
            logger.warning(f"MongoDB连接失败（可选服务，不影响应用启动）: {e}")
    else:
        logger.warning("MongoDB未配置或连接失败，部分功能可能不可用")
    
    # 测试Redis连接（可选）
    if redis_client:
        try:
            redis_client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.warning(f"Redis连接失败（可选服务，不影响应用启动）: {e}")
    else:
        logger.warning("Redis未配置或连接失败，Celery任务功能可能不可用")
    
    # 创建表（同步方式）
    try:
        from app.models import brand, crawl_task, analysis_task, report
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建完成")
    except Exception as e:
        logger.warning(f"自动创建数据库表失败: {e}")
        logger.warning("如果表已存在，可以忽略此警告。")


def get_db():
    """获取同步数据库会话 (Deprecated: 请尽量使用 get_async_db)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """获取异步数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_mongodb():
    """获取MongoDB数据库"""
    if mongodb is None:
        raise RuntimeError("MongoDB未连接，请启动MongoDB服务")
    return mongodb


def get_redis():
    """获取Redis客户端"""
    if redis_client is None:
        raise RuntimeError("Redis未连接，请启动Redis服务")
    return redis_client
