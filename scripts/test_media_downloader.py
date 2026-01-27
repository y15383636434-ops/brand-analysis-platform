import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.media_downloader import media_downloader
from app.core.database import get_mongodb
from config import settings

async def test_downloader():
    print("Testing MediaDownloader...")
    
    # 1. Get a video URL from MongoDB
    mongodb = get_mongodb()
    
    # Get latest 20 items and filter in python
    cursor = mongodb.raw_data.find({"platform": "douyin"}).sort("_id", -1).limit(20)
    items = list(cursor)
    
    item = None
    video_url = None
    
    for i in items:
        raw = i.get("raw_data", {})
        # Try different fields
        url = raw.get("video_download_url")
        if not url:
            # Try nested
            vid = raw.get("video", {})
            if isinstance(vid, dict):
                play_addr = vid.get("play_addr", {})
                if isinstance(play_addr, dict):
                    url_list = play_addr.get("url_list", [])
                    if url_list:
                        url = url_list[-1]
        
        if url:
            item = i
            video_url = url
            break
    
    if not item:
        print("No douyin video found in DB with URL.")
        return

    print(f"Found item: {item.get('content_id')}")
    
    # Extract URL manually to test
    raw = item.get("raw_data", {})
    video_url = raw.get("video_download_url")
    if not video_url:
        url_list = raw.get("video", {}).get("play_addr", {}).get("url_list", [])
        if url_list:
            video_url = url_list[-1] # Use last one
            
    print(f"Video URL: {video_url[:50]}...")
    
    if not video_url:
        print("Could not extract URL.")
        return

    # 2. Test download
    # Use real ID to test MediaCrawler fallback
    test_id = str(item.get("content_id"))
    
    # Force fallback by providing an invalid URL
    print(f"Attempting download for {test_id} with INVALID URL to trigger fallback...")
    result = await media_downloader.download_item_media("douyin", test_id, "https://invalid-url.com/video.mp4")
    
    print(f"Download result: {result}")
    
    # 3. Verify file
    if result["success"]:
        path = Path(result["path"])
        if path.exists():
            size = path.stat().st_size
            print(f"File exists! Size: {size / 1024 / 1024:.2f} MB")
            print(f"Path: {path}")
            
            # Clean up
            try:
                path.unlink()
                path.parent.rmdir()
                print("Cleaned up test file.")
            except:
                pass
        else:
            print("Error: Result says success but file not found.")
    else:
        print("Download failed.")

if __name__ == "__main__":
    asyncio.run(test_downloader())
