"""
FastAPI 主应用入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from loguru import logger
import sys
import os
from pathlib import Path
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
from app.api.v1 import brands, crawl_tasks, analysis_tasks, reports, data_viewer, crawler_ui, mediacrawler_ui, data_analysis, dashboard, media
from app.core.database import init_db
from app.core.logger import setup_logging

# 配置日志
logger = setup_logging()
# Force reload trigger
logger.info("Server reloading for configuration update")


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
        from app.core.database import engine, async_engine, mongo_client, redis_client
        
        # 关闭同步数据库连接
        if engine:
            engine.dispose()
            logger.info("同步数据库连接池已关闭")
            
        # 关闭异步数据库连接
        if async_engine:
            await async_engine.dispose()
            logger.info("异步数据库连接池已关闭")
            
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

# 挂载静态文件目录
# 1. 媒体数据目录 (爬取的图片/视频)
# 优先使用 MediaCrawler 的数据目录，因为视频默认下载到那里
# 同时确保项目自己的数据目录也被挂载，以防同步脚本已运行
mediacrawler_path = settings.MEDIACRAWLER_PATH
project_data_path = settings.DATA_DIR / "crawled_data"

# 1.1 挂载 MediaCrawler 的数据目录
if mediacrawler_path:
    if mediacrawler_path.startswith("./") or mediacrawler_path.startswith(".\\"):
        project_root = Path(__file__).resolve().parent.parent
        mc_path = (project_root / mediacrawler_path.lstrip("./\\")).resolve()
    else:
        mc_path = Path(mediacrawler_path)
    
    mc_data_path = mc_path / "data" / "crawled_data"
    if mc_data_path.exists():
        logger.info(f"挂载 MediaCrawler 数据目录: {mc_data_path}")
        app.mount("/media/mc", StaticFiles(directory=str(mc_data_path)), name="media_mc")

# 1.2 挂载项目自己的数据目录 (同步后的文件)
if not project_data_path.exists():
    project_data_path.mkdir(parents=True, exist_ok=True)

logger.info(f"挂载项目数据目录: {project_data_path}")
app.mount("/media/local", StaticFiles(directory=str(project_data_path)), name="media_local")

# 为了兼容旧代码，保留 /media 挂载，优先指向本地同步目录，如果为空则指向 MC 目录
# 这样前端引用 /media/xxx 时能找到文件
final_media_path = project_data_path
if not any(project_data_path.iterdir()) and mediacrawler_path:
     if mc_data_path.exists():
         final_media_path = mc_data_path

app.mount("/media", StaticFiles(directory=str(final_media_path)), name="media")

# 2. 前端模板使用的静态资源 (CSS/JS)
# 如果有 static 目录的话
static_path = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

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
app.include_router(media.router, prefix=settings.API_V1_PREFIX, tags=["媒体管理"])
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
        "version": settings.PROJECT_VERSION,
        "mounts": {
             "local": str(project_data_path),
             "exists": project_data_path.exists()
        }
    }


@app.get("/.well-known/appspecific/com.chrome.devtools.json")
async def chrome_devtools_config():
    """
    处理 Chrome DevTools 请求的 404 错误
    这是一个浏览器尝试加载的配置文件，在开发环境中通常不存在，添加此路由以消除 404 日志噪音
    """
    return JSONResponse(content={}, status_code=200)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """
    处理 favicon.ico 请求，防止 404 错误
    """
    return JSONResponse(content={}, status_code=200)


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


from fastapi.exceptions import RequestValidationError, HTTPException

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """处理HTTP异常，统一返回JSON格式"""
    # 对于分析相关的API，返回统一的JSON格式
    if "/brands/" in str(request.url) and "/analysis" in str(request.url):
        return JSONResponse(
            status_code=200,  # 统一返回200，用code表示业务状态
            content={
                "code": exc.status_code,
                "message": exc.detail or "请求失败",
                "data": {
                    "error": exc.detail or "请求失败",
                    "message": exc.detail or "请求失败"
                }
            }
        )
    
    # 其他API保持原有格式
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail or "请求失败",
            "detail": exc.detail
        }
    )


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
        reload_excludes=["MediaCrawler/**", "crawl_scripts/**"] if settings.DEBUG else None
    )
