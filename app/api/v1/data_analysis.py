"""
数据分析API
提供数据整理和AI分析功能
"""
from fastapi import APIRouter, Request, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List
from pathlib import Path
from loguru import logger
import sys
from pydantic import BaseModel

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.data_processor import data_processor
from app.services.ai_service import ai_service
from app.tasks.analysis_tasks import analyze_brand_task
from app.core.database import get_mongodb

router = APIRouter()

# 模板目录
templates_dir = project_root / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# MediaCrawler路径
MEDIACRAWLER_PATH = project_root / "MediaCrawler"

# 平台映射
PLATFORM_MAP = {
    "xhs": "小红书",
    "douyin": "抖音",
    "weibo": "微博",
    "zhihu": "知乎",
    "bilibili": "B站",
    "kuaishou": "快手",
    "tieba": "百度贴吧",
}


# MediaCrawler实际数据目录名映射
MEDIACRAWLER_DATA_DIR_MAP = {
    "xhs": "xhs",              # 小红书
    "douyin": "douyin",        # 抖音
    "weibo": "weibo",          # 微博
    "zhihu": "zhihu",          # 知乎
    "bilibili": "bili",        # B站
    "bili": "bili",            # B站（兼容）
    "kuaishou": "kuaishou",    # 快手
    "ks": "kuaishou",          # 快手（兼容）
    "tieba": "tieba",          # 百度贴吧
}

def get_actual_data_dir(mediacrawler_path: Path, platform_code: str) -> Path:
    """获取实际的数据目录"""
    base_dir = mediacrawler_path / "data"
    actual_dir_name = MEDIACRAWLER_DATA_DIR_MAP.get(platform_code, platform_code)
    standard_dir = base_dir / actual_dir_name
    
    if standard_dir.exists():
        return standard_dir
        
    # 兼容性检查
    alt_names = {"ks": "kuaishou", "dy": "douyin", "wb": "weibo"}
    if platform_code in alt_names:
        alt_dir = base_dir / alt_names[platform_code]
        if alt_dir.exists():
            return alt_dir
            
    return standard_dir

@router.get("/data-analysis", response_class=HTMLResponse)
async def data_analysis_ui(request: Request):
    """数据分析界面"""
    platforms = [
        {"code": code, "name": name}
        for code, name in PLATFORM_MAP.items()
    ]
    return templates.TemplateResponse("data_analysis.html", {
        "request": request,
        "platforms": platforms
    })


@router.get("/data-analysis/files")
async def list_analysis_files(
    platform: str = Query(..., description="平台代码"),
    data_type: str = Query("contents", description="数据类型: contents或comments")
):
    """获取可用于分析的文件列表"""
    try:
        if platform not in PLATFORM_MAP:
            return JSONResponse({
                "success": False,
                "error": "无效的平台"
            }, status_code=400)
        
        # 使用本地定义的 get_actual_data_dir，避免导入问题
        actual_data_dir = get_actual_data_dir(MEDIACRAWLER_PATH, platform)
        data_dir = actual_data_dir / "json"
        
        logger.info(f"正在查找文件: platform={platform}, path={data_dir}")
        
        if not data_dir.exists():
            logger.warning(f"数据目录不存在: {data_dir}")
            return JSONResponse({
                "success": True,
                "files": [],
                "message": "数据目录不存在"
            })
        
        # 查找JSON文件
        if data_type == "all":
            pattern = "*.json"
        else:
            # 兼容旧格式 (search_xxx) 和新格式 (platform_keyword_xxx)
            pattern = f"*_{data_type}_*.json"
            
        json_files = list(data_dir.glob(pattern))
        logger.info(f"查询文件结果: dir={data_dir}, pattern={pattern}, found={len(json_files)}")
        
        files_info = []
        for file_path in sorted(json_files, key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                stat = file_path.stat()
                files_info.append({
                    "filename": file_path.name,
                    "size": stat.st_size,
                    "modified_time": stat.st_mtime,
                    "path": str(file_path.relative_to(MEDIACRAWLER_PATH))
                })
            except Exception as e:
                logger.error(f"读取文件信息失败: {e}")
        
        return JSONResponse({
            "success": True,
            "files": files_info,
            "platform": platform,
            "data_type": data_type
        })
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.post("/data-analysis/process")
async def process_data(request: Request):
    """处理数据并启动AI分析（支持单平台和跨平台）"""
    # 使用本地定义的 get_actual_data_dir
    # from app.api.v1.mediacrawler_ui import get_actual_data_dir
    
    try:
        # 从FormData中获取参数
        form_data = await request.form()
    except Exception as e:
        logger.error(f"解析FormData失败: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": f"请求格式错误: {str(e)}"
        }, status_code=422)
    
    # 获取参数，使用默认值
    platform = form_data.get("platform")
    filenames = form_data.get("filenames")
    files_json = form_data.get("files_json")
    include_comments_str = form_data.get("include_comments", "true")
    analysis_type = form_data.get("analysis_type", "comprehensive")
    cross_platform_str = form_data.get("cross_platform", "false")
    
    # 处理可能为None的值
    if platform is not None:
        platform = str(platform).strip() if platform else None
        if platform in ['null', 'undefined']:
            platform = None
    if filenames is not None:
        filenames = str(filenames).strip() if filenames else None
    if files_json is not None:
        files_json = str(files_json).strip() if files_json else None
    if include_comments_str:
        include_comments_str = str(include_comments_str).strip()
    if analysis_type:
        analysis_type = str(analysis_type).strip()
    if cross_platform_str:
        cross_platform_str = str(cross_platform_str).strip()
    
    # 转换字符串为布尔值
    include_comments_bool = include_comments_str.lower() in ("true", "1", "yes", "on") if include_comments_str else True
    cross_platform_bool = cross_platform_str.lower() in ("true", "1", "yes", "on") if cross_platform_str else False
    
    # 记录接收到的参数（用于调试）
    logger.info(f"接收到的参数: platform={platform}, filenames={filenames}, files_json={files_json[:100] if files_json else None}, cross_platform={cross_platform_str}")
    
    try:
        # 判断是否为跨平台分析：cross_platform为true且files_json不为空
        if cross_platform_bool:
            # 跨平台分析模式
            if not files_json or not files_json.strip():
                return JSONResponse({
                    "success": False,
                    "error": "跨平台分析需要提供files_json参数"
                }, status_code=400)
            # 跨平台分析
            import json
            try:
                files_by_platform = json.loads(files_json)
            except json.JSONDecodeError as e:
                logger.error(f"解析files_json失败: {e}, files_json={files_json}")
                return JSONResponse({
                    "success": False,
                    "error": f"files_json格式错误: {str(e)}"
                }, status_code=400)
            
            if not files_by_platform:
                return JSONResponse({
                    "success": False,
                    "error": "请至少选择一个文件"
                })
            
            # 构建文件路径
            file_paths_by_platform = {}
            for platform_code, filename_list in files_by_platform.items():
                if platform_code not in PLATFORM_MAP:
                    logger.warning(f"无效的平台: {platform_code}")
                    continue
                
                actual_data_dir = get_actual_data_dir(MEDIACRAWLER_PATH, platform_code)
                platform_file_paths = []
                
                for filename in filename_list:
                    file_path = actual_data_dir / "json" / filename
                    if file_path.exists():
                        platform_file_paths.append(file_path)
                    else:
                        logger.warning(f"文件不存在: {file_path}")
                
                if platform_file_paths:
                    file_paths_by_platform[platform_code] = platform_file_paths
            
            if not file_paths_by_platform:
                return JSONResponse({
                    "success": False,
                    "error": "没有找到有效的文件"
                })
            
            # 处理跨平台数据
            logger.info(f"开始跨平台处理数据: platforms={list(file_paths_by_platform.keys())}, total_files={sum(len(files) for files in file_paths_by_platform.values())}")
            processed_data = data_processor.process_cross_platform_files(
                file_paths_by_platform,
                include_comments_bool
            )
            
            platform_names = [PLATFORM_MAP.get(p, p) for p in processed_data["platforms"]]
            brand_name = f"跨平台综合分析（{', '.join(platform_names)}）"
            
        else:
            # 单平台分析（原有逻辑）
            if not platform or not platform.strip():
                return JSONResponse({
                    "success": False,
                    "error": "单平台分析需要提供platform参数"
                }, status_code=400)
            
            if platform not in PLATFORM_MAP:
                return JSONResponse({
                    "success": False,
                    "error": f"无效的平台: {platform}"
                }, status_code=400)
            
            if not filenames or not filenames.strip():
                return JSONResponse({
                    "success": False,
                    "error": "单平台分析需要提供filenames参数"
                }, status_code=400)
            
            # 解析文件名列表
            filename_list = [f.strip() for f in filenames.split(",") if f.strip()]
            if not filename_list:
                return JSONResponse({
                    "success": False,
                    "error": "请至少选择一个文件"
                })
            
            # 构建文件路径
            actual_data_dir = get_actual_data_dir(MEDIACRAWLER_PATH, platform)
            file_paths = []
            for filename in filename_list:
                file_path = actual_data_dir / "json" / filename
                if not file_path.exists():
                    logger.warning(f"文件不存在: {file_path}")
                    continue
                file_paths.append(file_path)
            
            if not file_paths:
                return JSONResponse({
                    "success": False,
                    "error": "没有找到有效的文件"
                })
            
            # 处理数据
            logger.info(f"开始处理数据: platform={platform}, files={len(file_paths)}")
            processed_data = data_processor.process_multiple_files(
                file_paths,
                platform,
                include_comments_bool
            )
            
            brand_name = f"{PLATFORM_MAP.get(platform, platform)}数据"
        
        if not processed_data["all_texts"]:
            return JSONResponse({
                "success": False,
                "error": "没有提取到可分析的文本数据"
            })
        
        # 执行AI分析
        logger.info(f"开始AI分析: {len(processed_data['all_texts'])}条文本")
        
        # 1. 情感分析
        sentiment_result = ai_service.batch_analyze_sentiment(processed_data["all_texts"])
        
        # 2. 关键词提取
        all_text = " ".join(processed_data["all_texts"])
        keywords = ai_service.extract_keywords(all_text, top_k=20, with_weight=True)
        
        # 3. 文本统计
        text_stats = ai_service.analyze_text_statistics(processed_data["all_texts"])
        
        # 3.5 互动数据统计
        interaction_stats = {
            "total_likes": 0,
            "total_comments": 0,
            "total_shares": 0,
            "by_platform": {}
        }
        
        raw_items = processed_data.get("raw_items", [])
        for item in raw_items:
            platform_code = item.get("platform", "unknown")
            likes = item.get("likes", 0) or 0
            comments = item.get("comments_count", 0) or 0
            shares = item.get("shares", 0) or 0
            
            # 总计
            interaction_stats["total_likes"] += likes
            interaction_stats["total_comments"] += comments
            interaction_stats["total_shares"] += shares
            
            # 按平台
            if platform_code not in interaction_stats["by_platform"]:
                interaction_stats["by_platform"][platform_code] = {
                    "likes": 0,
                    "comments": 0,
                    "shares": 0,
                    "count": 0
                }
            
            p_stats = interaction_stats["by_platform"][platform_code]
            p_stats["likes"] += likes
            p_stats["comments"] += comments
            p_stats["shares"] += shares
            p_stats["count"] += 1
        
        # 4. LLM深度分析
        data_summary = {
            "total_count": len(processed_data["all_texts"]),
            "sentiment_distribution": sentiment_result.get("distribution", {}),
            "avg_sentiment_score": sentiment_result.get("avg_score", 0.5),
            "keywords": keywords
        }
        
        # 如果是跨平台分析，添加平台统计信息
        if cross_platform_bool and "platform_stats" in processed_data:
            data_summary["platform_stats"] = processed_data["platform_stats"]
        
        # 调用LLM分析
        import asyncio
        llm_result = await ai_service.analyze_with_llm(
            brand_name=brand_name,
            data_summary=data_summary,
            analysis_type=analysis_type
        )
        
        # 组装分析结果
        if cross_platform_bool:
            analysis_result = {
                "platforms": processed_data["platforms"],
                "platform_names": [PLATFORM_MAP.get(p, p) for p in processed_data["platforms"]],
                "is_cross_platform": True,
                "processed_data": {
                    "total_items": processed_data["total_items"],
                    "total_texts": len(processed_data["texts"]),
                    "total_comments": len(processed_data["comments"]),
                    "file_count": processed_data["file_count"],
                    "platform_stats": processed_data.get("platform_stats", {})
                },
                "sentiment_analysis": sentiment_result,
                "keywords": keywords,
                "text_statistics": text_stats,
                "interaction_statistics": interaction_stats,
                "llm_insights": llm_result,
                "processed_at": processed_data["processed_at"]
            }
        else:
            analysis_result = {
                "platform": platform,
                "platform_name": PLATFORM_MAP.get(platform, platform),
                "is_cross_platform": False,
                "processed_data": {
                    "total_items": processed_data["total_items"],
                    "total_texts": len(processed_data["texts"]),
                    "total_comments": len(processed_data["comments"]),
                    "file_count": processed_data["file_count"]
                },
                "sentiment_analysis": sentiment_result,
                "keywords": keywords,
                "text_statistics": text_stats,
                "interaction_statistics": interaction_stats,
                "llm_insights": llm_result,
                "processed_at": processed_data["processed_at"]
            }
        
        # 保存到MongoDB（可选）
        try:
            mongodb = get_mongodb()
            result_doc = {
                "platform": platform if not cross_platform_bool else "cross_platform",
                "platforms": processed_data.get("platforms", [platform] if platform else []),
                "is_cross_platform": cross_platform_bool,
                "analysis_type": analysis_type,
                "result": analysis_result,
                "created_at": processed_data["processed_at"]
            }
            insert_result = mongodb.data_analysis_results.insert_one(result_doc)
            result_id = str(insert_result.inserted_id)
            logger.info(f"分析结果已保存到MongoDB, ID: {result_id}")
        except Exception as e:
            logger.warning(f"保存到MongoDB失败: {e}")
            result_id = None
        
        return JSONResponse({
            "success": True,
            "result": analysis_result,
            "result_id": result_id
        })
        
    except Exception as e:
        logger.error(f"处理数据失败: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": f"处理失败: {str(e)}"
        }, status_code=500)


@router.get("/data-analysis/result", response_class=HTMLResponse)
async def view_analysis_result(
    request: Request,
    platform: Optional[str] = Query(None),
    brand_id: Optional[int] = Query(None)
):
    """查看分析结果页面"""
    return templates.TemplateResponse("analysis_result.html", {
        "request": request,
        "platform": platform,
        "platform_name": PLATFORM_MAP.get(platform, "全部") if platform else "全部",
        "brand_id": brand_id
    })


@router.get("/data-analysis/result/list")
async def list_analysis_results(
    platform: Optional[str] = Query(None),
    result_id: Optional[str] = Query(None)
):
    """获取分析结果列表"""
    try:
        mongodb = get_mongodb()
        
        query = {}
        
        if result_id:
            # 如果提供了result_id，直接按ID查询
            from bson import ObjectId
            try:
                query["_id"] = ObjectId(result_id)
            except Exception as e:
                return JSONResponse({
                    "success": False,
                    "error": f"无效的ID格式: {str(e)}"
                }, status_code=400)
        elif platform:
            # 兼容旧数据（只有platform字段）和新数据（platforms数组）
            query["$or"] = [
                {"platform": platform},
                {"platforms": platform}
            ]
            
        logger.info(f"查询分析结果: query={query}")
        
        results = list(mongodb.data_analysis_results.find(query)
                      .sort("created_at", -1)
                      .limit(50))
        
        logger.info(f"查询到 {len(results)} 条分析结果")
        
        # 转换ObjectId
        for result in results:
            result["_id"] = str(result["_id"])
            # 确保result字段存在，如果不存在，构造一个
            if "result" not in result:
                result["result"] = {
                    "processed_data": {
                        "total_items": 0, 
                        "total_texts": 0, 
                        "total_comments": 0, 
                        "file_count": 0
                    },
                    "sentiment_analysis": None,
                    "keywords": [],
                    "llm_insights": {"insights": "数据结构旧版本，无法显示详情"}
                }
        
        return JSONResponse({
            "success": True,
            "results": results
        })
    except Exception as e:
        logger.error(f"获取分析结果失败: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


class VideoAnalysisRequest(BaseModel):
    video_url: str
    item_id: Optional[str] = None
    platform: Optional[str] = None
    prompt: Optional[str] = None

@router.post("/data-analysis/video")
async def analyze_video(request: VideoAnalysisRequest):
    """分析视频内容"""
    if not request.video_url:
        return JSONResponse({"success": False, "error": "视频URL不能为空"}, status_code=400)
    
    video_source = request.video_url
    
    # 尝试查找本地视频文件，避免下载
    if request.item_id and request.platform:
        try:
            from config import settings
            
            # 映射平台名称到目录名
            platform_code = MEDIACRAWLER_DATA_DIR_MAP.get(request.platform, request.platform)
            # 常见变体
            if platform_code == "dy": platform_code = "douyin"
            if platform_code == "ks": platform_code = "kuaishou"
            if platform_code == "wb": platform_code = "weibo"
            
            # 优先检查项目数据目录 (settings.DATA_DIR)
            # 路径: data/crawled_data/{platform}/{item_id}/video.mp4
            project_data_file = settings.DATA_DIR / "crawled_data" / platform_code / str(request.item_id) / "video.mp4"
            
            # 其次检查 MediaCrawler 数据目录
            mc_data_file = MEDIACRAWLER_PATH / "data" / "crawled_data" / platform_code / str(request.item_id) / "video.mp4"
            
            local_file = None
            if project_data_file.exists():
                local_file = project_data_file
            elif mc_data_file.exists():
                local_file = mc_data_file
            
            if local_file:
                logger.info(f"找到本地视频文件: {local_file}")
                video_source = str(local_file)
            else:
                logger.debug(f"本地视频文件不存在: {project_data_file} 或 {mc_data_file}")
                # 尝试查找图片序列（针对图文笔记）
                # 同样检查两个位置
                folder_paths = [
                    settings.DATA_DIR / "crawled_data" / platform_code / str(request.item_id),
                    MEDIACRAWLER_PATH / "data" / "crawled_data" / platform_code / str(request.item_id)
                ]
                
                for folder_path in folder_paths:
                    if folder_path.exists():
                        images = list(folder_path.glob("*.jpeg")) + list(folder_path.glob("*.jpg")) + list(folder_path.glob("*.png"))
                        if images:
                            logger.info(f"找到本地图片序列 ({len(images)}张): {folder_path}")
                            # 按文件名排序
                            images.sort(key=lambda x: x.name)
                            image_paths = [str(img) for img in images]
                            # 直接进行图片分析并返回
                            result = await ai_service.analyze_image_sequence(image_paths, request.prompt)
                            return JSONResponse(result)
        except Exception as e:
            logger.warning(f"查找本地视频失败: {e}")
    
    result = await ai_service.analyze_video_content(video_source, request.prompt)
    return JSONResponse(result)
