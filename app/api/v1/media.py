"""
Media Management API
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from loguru import logger
import asyncio

from app.core.database import get_db, get_mongodb
from app.services.media_downloader import media_downloader
from app.models.brand import Brand

router = APIRouter()

@router.post("/media/download/{platform}/{item_id}")
async def download_media(
    platform: str, 
    item_id: str, 
    background_tasks: BackgroundTasks,
    video_url: str = None
):
    """
    Trigger media download for a specific item.
    Optional video_url can be provided if known.
    """
    async def _do_download(plat, i_id, v_url):
        logger.info(f"Starting background download for {plat}/{i_id}")
        result = await media_downloader.download_item_media(plat, i_id, v_url)
        logger.info(f"Download result for {plat}/{i_id}: {result}")
        
        # If successful, update MongoDB
        if result.get("success"):
            try:
                mongodb = get_mongodb()
                # Determine platform code for DB query
                p_code = plat
                if plat == "dy": p_code = "douyin"
                
                # Update document
                # Try to match by various ID fields
                query = {
                    "platform": p_code,
                    "$or": [
                        {"content_id": i_id},
                        {"aweme_id": i_id},
                        {"video_id": i_id},
                        {"id": i_id}
                    ]
                }
                
                update = {
                    "$set": {
                        "video_path": f"{p_code}/{i_id}/video.mp4",
                        "media_downloaded": True
                    }
                }
                
                res = mongodb.raw_data.update_one(query, update)
                logger.info(f"Updated MongoDB document: {res.modified_count}")
                
            except Exception as e:
                logger.error(f"Failed to update DB after download: {e}")

    background_tasks.add_task(_do_download, platform, item_id, video_url)
    
    return {
        "code": 200,
        "message": "Download task queued",
        "data": {
            "platform": platform,
            "item_id": item_id
        }
    }

@router.post("/media/download-batch")
async def batch_download_missing(
    background_tasks: BackgroundTasks,
    platform: str = "douyin",
    limit: int = 10
):
    """
    Scan database for items missing media and queue downloads.
    """
    mongodb = get_mongodb()
    query = {
        "platform": platform,
        "video_path": None, # or check existence? 
        # For now assume if video_path is null/missing in DB, it needs download
        # Or better, check if we have raw_data but no video_path
        "raw_data": {"$exists": True}
    }
    
    cursor = mongodb.raw_data.find(query).limit(limit)
    items = list(cursor)
    
    tasks_created = 0
    for item in items:
        item_id = item.get("content_id") or item.get("aweme_id") or item.get("video_id")
        if not item_id:
            continue
            
        # Extract URL from raw_data if possible
        raw = item.get("raw_data", {})
        video_url = raw.get("video_download_url")
        
        # Douyin logic
        if not video_url and platform == "douyin":
             vid_info = raw.get("video", {})
             if vid_info:
                 # Reuse downloader logic to extract
                 video_url = media_downloader.douyin._extract_video_url(vid_info)
        
        background_tasks.add_task(media_downloader.download_item_media, platform, item_id, video_url)
        tasks_created += 1
        
    return {
        "code": 200,
        "message": f"Queued {tasks_created} download tasks",
        "data": {
            "count": tasks_created
        }
    }
