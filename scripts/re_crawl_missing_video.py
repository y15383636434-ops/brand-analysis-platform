import os
import sys
import asyncio
import httpx
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.crawler_service import CrawlerService
from config import settings

async def download_video(url, output_path, referer="https://www.douyin.com/"):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": referer,
        "Origin": "https://www.douyin.com"
    }
    
    print(f"Downloading video from {url}...")
    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=60.0) as client:
            response = await client.get(url)
            print(f"Response status: {response.status_code}")
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                print(f"Saved to {output_path}")
                return True
            else:
                print(f"Failed to download. Status: {response.status_code}")
                return False
    except Exception as e:
        print(f"Download exception: {e}")
        return False

async def re_crawl():
    print("Initializing CrawlerService...")
    service = CrawlerService()
    
    video_id = "7526514210193853755"
    target_url = f"https://www.douyin.com/video/{video_id}"
    
    print(f"Target URL: {target_url}")
    
    try:
        # 1. Run MediaCrawler to get the video URL (even if download fails)
        print("Starting crawl to get metadata...")
        result = service.crawl_platform(
            platform="douyin",
            keywords=[], 
            crawl_type="detail",
            target_url=target_url,
            enable_media_download=False, # We download manually
            max_items=1
        )
        
        items = result.get("items", [])
        print(f"Got {len(items)} items")
        
        target_item = None
        for item in items:
            # Check ID
            iid = item.get("aweme_id") or item.get("id") or item.get("video_id")
            if str(iid) == video_id:
                target_item = item
                break
        
        if not target_item and items:
            print("Target ID not found in items, using first item as fallback")
            target_item = items[0]
            
        if target_item:
            print(f"Found item keys: {target_item.keys()}")
            
            # Extract video URL
            video_url = None
            if "video_download_url" in target_item:
                video_url = target_item["video_download_url"]
            elif "video" in target_item and isinstance(target_item["video"], dict):
                play_addr = target_item["video"].get("play_addr", {})
                url_list = play_addr.get("url_list", [])
                if url_list:
                    video_url = url_list[0] # Usually the first one is good
            
            if not video_url and "video" in target_item:
                 # sometimes it's directly in video field if flattened?
                 pass

            if video_url:
                print(f"Found Video URL: {video_url}")
                
                # Define output path
                output_dir = service.data_dir / "douyin" / video_id
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / "video.mp4"
                
                # Download
                success = await download_video(video_url, output_path)
                
                if success:
                    print("Video downloaded successfully!")
                    
                    # Update database with video path
                    # service.save_crawled_data will update the path if we call it again?
                    # or we can manually update DB.
                    # But actually service.save_crawled_data calls are already done inside crawl_platform?
                    # No, crawl_platform returns the result, the caller (task) calls save_crawled_data.
                    # But here I am calling service.crawl_platform directly.
                    # Wait, crawler_service.py: save_crawled_data is NOT called inside crawl_platform.
                    
                    # So I should call save_crawled_data to update DB.
                    # I need a mongodb instance.
                    from app.core.database import get_mongodb
                    mongodb = get_mongodb()
                    
                    # Update the item with video_path
                    # CrawlerService.save_crawled_data logic checks for local files.
                    # Since I saved the file to the expected location, it should pick it up!
                    
                    print("Saving metadata to DB...")
                    service.save_crawled_data(
                        brand_id=0, # Manual task
                        task_id=0,
                        platform="douyin",
                        data={"items": [target_item]},
                        mongodb=mongodb
                    )
                    print("DB updated.")
                    
            else:
                print("Could not find video URL in item")
        else:
            print("No items found")
        
    except Exception as e:
        print(f"Crawl failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(re_crawl())
