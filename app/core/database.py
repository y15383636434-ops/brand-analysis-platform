"""
数据库连接和初始化
"""
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from pymongo import MongoClient
from redis import Redis
from loguru import logger

from config import settings

# MySQL数据库
SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
    f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
    f"?charset=utf8mb4"
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=NullPool,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

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
    # 测试MySQL连接（必需）
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("MySQL连接成功")
    except Exception as e:
        logger.error(f"MySQL连接失败（必需服务）: {e}")
        raise  # MySQL是必需的，连接失败要抛出异常
    
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
    
    # 创建表（如果不存在）
    # 注意：由于MySQL权限问题，表创建可能失败，但不影响应用启动
    try:
        from app.models import brand, crawl_task, analysis_task, report
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建完成")
    except Exception as e:
        # 表创建失败可能是权限问题或表已存在，记录警告但不阻止启动
        logger.warning(f"自动创建数据库表失败: {e}")
        logger.warning("这可能是MySQL权限问题。如果表已存在，可以忽略此警告。")
        logger.warning("如果表不存在，请参考文档手动创建表，或联系数据库管理员修复权限。")
        # 不抛出异常，允许应用继续启动


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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

