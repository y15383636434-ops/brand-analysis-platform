"""
项目配置文件
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 项目基础信息
    PROJECT_NAME: str = "品牌分析系统"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # 路径配置
    BASE_DIR: Path = Path(__file__).resolve().parent
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # 数据库配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "root123456"
    MYSQL_DATABASE: str = "brand_analysis"
    
    # MongoDB配置
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_DATABASE: str = "brand_analysis"
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # AI配置 - LLM聚合网关（优先使用）
    # 基于 OneAPI/NewAPI 的统一LLM接口网关
    # 支持动态切换 GPT-4o, Claude 3.5, Gemini 等多种模型
    LLM_API_BASE: Optional[str] = None  # LLM聚合网关地址，例如: https://xy.xiaoxu030.xyz:8888/v1
    LLM_API_KEY: Optional[str] = None   # 聚合服务的分发令牌（通常以 sk- 开头）
    LLM_MODEL_NAME: Optional[str] = None  # 默认使用的模型名称，例如: gpt-4o-mini
    
    # OpenAI配置（直接调用，可选）
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    
    # Anthropic配置（直接调用，可选）
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    
    # Google Gemini配置（直接调用，可选）
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    
    # 本地LLM配置（可选）
    LOCAL_LLM_URL: Optional[str] = None
    LOCAL_LLM_MODEL: Optional[str] = None
    
    # 文件存储
    UPLOAD_DIR: Path = Path("uploads") if Path("uploads").is_absolute() else Path(__file__).resolve().parent / "uploads"
    REPORT_DIR: Path = Path("reports") if Path("reports").is_absolute() else Path(__file__).resolve().parent / "reports"
    DATA_DIR: Path = Path("data") if Path("data").is_absolute() else Path(__file__).resolve().parent / "data"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = str(Path(__file__).resolve().parent / "logs" / "app.log")
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 爬虫配置
    CRAWL_MAX_ITEMS: int = 100
    CRAWL_INCLUDE_COMMENTS: bool = True
    CRAWL_TIMEOUT: int = 300
    
    # MediaCrawler配置
    # 如果MediaCrawler在项目目录中，使用相对路径: "./MediaCrawler"
    # 如果在其他位置，使用绝对路径: r"C:\path\to\MediaCrawler"
    MEDIACRAWLER_PATH: Optional[str] = "./MediaCrawler"  # 默认使用项目目录中的MediaCrawler
    MEDIACRAWLER_PYTHON: Optional[str] = None  # 如果MediaCrawler有独立Python环境，指定路径
    USE_REAL_CRAWLER: bool = True  # 是否使用真实爬虫（已废弃，始终使用真实爬虫）
    FORCE_REAL_CRAWL: bool = True  # 强制使用真实爬虫（即使失败也不降级到模拟数据，已默认启用）
    
    # 分析配置
    ANALYSIS_SENTIMENT_ENABLED: bool = True
    ANALYSIS_TOPICS_ENABLED: bool = True
    ANALYSIS_KEYWORDS_ENABLED: bool = True
    ANALYSIS_INSIGHTS_ENABLED: bool = True
    
    # 报告配置
    REPORT_TEMPLATE_DIR: Path = Path("templates/reports") if Path("templates/reports").is_absolute() else Path(__file__).resolve().parent / "templates" / "reports"
    REPORT_OUTPUT_DIR: Path = Path("reports") if Path("reports").is_absolute() else Path(__file__).resolve().parent / "reports"
    REPORT_DEFAULT_FORMAT: str = "pdf"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建必要的目录
settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.REPORT_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
Path(settings.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
settings.REPORT_TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

