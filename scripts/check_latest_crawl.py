import sys
import os
import asyncio
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_mongodb
from config import settings

def check_latest_items(limit=10):
    print(f"Checking latest {limit} items in MongoDB...")
    mongodb = get_mongodb()
    
    # Sort by _id desc (roughly creation time) or crawled_at
    cursor = mongodb.raw_data.find({}).sort("_id", -1).limit(limit)
    items = list(cursor)
    
    print(f"Found {len(items)} items.")
    
    for i, item in enumerate(items):
        item_id = item.get("content_id") or item.get("aweme_id") or item.get("video_id")
        platform = item.get("platform")
        title = item.get("title", "No Title")[:30]
        video_path = item.get("video_path")
        
        print(f"\n[{i+1}] ID: {item_id} | Platform: {platform}")
        print(f"    Title: {title}")
        print(f"    Video Path (DB): {video_path}")
        
        # Check if file exists
        if video_path:
            # Check project data dir
            project_file = settings.DATA_DIR / "crawled_data" / video_path
            
            # Check MediaCrawler dir (if path is relative)
            # video_path is usually "douyin/ID/video.mp4"
            mc_path = Path(settings.MEDIACRAWLER_PATH) / "data" / "crawled_data" / video_path
            
            exists_proj = project_file.exists()
            exists_mc = mc_path.exists()
            
            print(f"    File Exists (Project): {exists_proj} -> {project_file}")
            print(f"    File Exists (MC): {exists_mc} -> {mc_path}")
        else:
            print("    No video path in DB")
            
        # Check raw data for download URL
        raw = item.get("raw_data", {})
        video_url = raw.get("video_download_url")
        if not video_url and "video" in raw:
             video_url = raw["video"].get("play_addr", {}).get("url_list", [None])[0]
        
        print(f"    Has Download URL: {bool(video_url)}")

if __name__ == "__main__":
    check_latest_items()
