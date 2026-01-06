"""
FastAPI 主应用入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys
import os
from datetime import datetime

# 设置UTF-8编码（Windows）
if sys.platform == 'win32':
    import io
    # 设置标准输出编码
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from config import settings
from app.api.v1 import brands, crawl_tasks, analysis_tasks, reports, data_viewer, crawler_ui, mediacrawler_ui, data_analysis, dashboard
from app.core.database import init_db

# 配置日志（设置UTF-8编码）
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL,
    colorize=True
)
logger.add(
    settings.LOG_FILE,
    rotation="10 MB",
    retention="7 days",
    level=settings.LOG_LEVEL,
    encoding='utf-8',
    errors='replace'
)


# ✅ 定义生命周期管理器 (替代 on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # ----------------- 启动逻辑 -----------------
    logger.info("=" * 50)
    logger.info(f"启动 {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}")
    logger.info("=" * 50)
    
    # 初始化数据库
    try:
        await init_db()
        logger.info("数据库连接成功")
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        # 根据实际情况决定是否抛出异常
        # raise
    
    logger.info("应用启动完成")
    
    yield  # 服务运行中...
    
    # ----------------- 关闭逻辑 -----------------
    logger.info("应用正在关闭...")
    
    # 清理所有运行中的爬取进程
    try:
        from app.api.v1.mediacrawler_ui import process_objects, process_lock, process_outputs
        import psutil
        
        with process_lock:
            if process_objects:
                logger.info(f"正在清理 {len(process_objects)} 个运行中的进程...")
                for process_id, process in list(process_objects.items()):
                    try:
                        if process.poll() is None:  # 进程还在运行
                            logger.info(f"终止进程 {process_id}...")
                            try:
                                # 使用 psutil 终止进程树
                                parent = psutil.Process(process.pid)
                                children = parent.children(recursive=True)
                                for child in children:
                                    try:
                                        child.terminate()
                                    except:
                                        pass
                                parent.terminate()
                                # 等待进程结束
                                try:
                                    parent.wait(timeout=3)
                                except psutil.TimeoutExpired:
                                    parent.kill()
                            except Exception as e:
                                logger.warning(f"终止进程 {process_id} 失败: {e}")
                                try:
                                    process.terminate()
                                except:
                                    pass
                            
                            # 更新状态
                            if process_id in process_outputs:
                                process_outputs[process_id]["status"] = "stopped"
                                process_outputs[process_id]["stopped_at"] = datetime.now().isoformat()
                    except Exception as e:
                        logger.warning(f"清理进程 {process_id} 时出错: {e}")
                
                # 清空进程对象
                process_objects.clear()
                logger.info("所有进程已清理完成")
    except ImportError:
        # 如果导入失败，忽略（可能模块未加载）
        pass
    except Exception as e:
        logger.warning(f"清理进程时出错: {e}")
    
    # 关闭数据库连接池、Redis连接等
    try:
        from app.core.database import engine, mongo_client, redis_client
        if engine:
            engine.dispose()
            logger.info("数据库连接池已关闭")
        if mongo_client:
            mongo_client.close()
            logger.info("MongoDB连接已关闭")
        if redis_client:
            redis_client.close()
            logger.info("Redis连接已关闭")
    except Exception as e:
        logger.warning(f"关闭数据库连接时出错: {e}")


# ✅ 在创建 app 时传入 lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="品牌分析系统 - 全网数据采集、AI分析和报告生成平台",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan  # <--- 绑定生命周期
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该设置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由 - HTML界面路由优先注册，避免与API路由冲突
# 数据展示界面（HTML路由，需要优先注册）
from app.api.v1 import data_display
app.include_router(data_display.router, prefix=settings.API_V1_PREFIX, tags=["数据展示"])

# API路由
app.include_router(brands.router, prefix=settings.API_V1_PREFIX, tags=["品牌管理"])
app.include_router(crawl_tasks.router, prefix=settings.API_V1_PREFIX, tags=["数据采集"])
app.include_router(analysis_tasks.router, prefix=settings.API_V1_PREFIX, tags=["数据分析"])
app.include_router(reports.router, prefix=settings.API_V1_PREFIX, tags=["报告生成"])
app.include_router(data_viewer.router, prefix=settings.API_V1_PREFIX, tags=["数据查看"])
app.include_router(crawler_ui.router, prefix=settings.API_V1_PREFIX, tags=["爬虫界面"])
app.include_router(mediacrawler_ui.router, prefix=settings.API_V1_PREFIX, tags=["MediaCrawler界面"])
app.include_router(data_analysis.router, prefix=settings.API_V1_PREFIX, tags=["数据分析"])

# Dashboard统一控制台 - 放在最后注册，避免路由冲突
app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX, tags=["统一控制台"])


@app.get("/")
async def root():
    """根路径 - 重定向到统一控制台"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"{settings.API_V1_PREFIX}/dashboard")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": settings.PROJECT_VERSION
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "error": str(exc) if settings.DEBUG else "Internal server error"
        }
    )


from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """处理422验证错误"""
    logger.error(f"请求验证失败: {exc.errors()}")
    errors = exc.errors()
    error_messages = []
    for error in errors:
        loc = " -> ".join(str(loc) for loc in error.get("loc", []))
        msg = error.get("msg", "验证失败")
        error_messages.append(f"{loc}: {msg}")
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "请求参数验证失败",
            "details": error_messages,
            "raw_errors": errors if settings.DEBUG else None
        }
    )


if __name__ == "__main__":
    import uvicorn
    # 确保UTF-8环境变量已设置
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        reload_exclude=["MediaCrawler/**", "crawl_scripts/**"] if settings.DEBUG else None
    )

