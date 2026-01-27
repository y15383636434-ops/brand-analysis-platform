import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.media_downloader import media_downloader
from app.core.database import get_mongodb
from loguru import logger

async def download_missing():
    print("Scanning for items with missing video files...")
    
    mongodb = get_mongodb()
    # Find items where video_path is missing but we have raw_data
    query = {
        "platform": "douyin",
        "video_path": None,
        "raw_data": {"$exists": True}
    }
    
    # Also check for items where video_path is set but file doesn't exist?
    # For now, just trust DB state or maybe reset it if needed.
    
    cursor = mongodb.raw_data.find(query)
    items = list(cursor)
    print(f"Found {len(items)} items to process.")
    
    success_count = 0
    fail_count = 0
    
    for item in items:
        item_id = item.get("content_id") or item.get("aweme_id") or item.get("video_id")
        if not item_id:
            continue
            
        print(f"Processing {item_id}...")
        
        # Extract URL
        raw = item.get("raw_data", {})
        video_url = raw.get("video_download_url")
        
        if not video_url:
            vid_info = raw.get("video", {})
            if vid_info:
                video_url = media_downloader.douyin._extract_video_url(vid_info)
            
        if not video_url:
            print(f"  - No video URL found in metadata for {item_id}")
            fail_count += 1
            continue
            
        # Download
        result = await media_downloader.download_item_media("douyin", item_id, video_url)
        
        if result.get("success"):
            print(f"  - Download SUCCESS: {result.get('path')}")
            success_count += 1
            
            # Update DB
            try:
                mongodb.raw_data.update_one(
                    {"_id": item["_id"]},
                    {"$set": {
                        "video_path": f"douyin/{item_id}/video.mp4",
                        "media_downloaded": True
                    }}
                )
            except Exception as e:
                print(f"  - Failed to update DB: {e}")
        else:
            print(f"  - Download FAILED: {result.get('message')}")
            fail_count += 1
            
    print(f"\nSummary: {success_count} succeeded, {fail_count} failed.")

if __name__ == "__main__":
    asyncio.run(download_missing())
