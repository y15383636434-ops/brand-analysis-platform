import os
import sys
import asyncio
import httpx
import time
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.crawler_service import CrawlerService
from app.core.database import get_mongodb
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

async def download_cover(cover_url, output_path):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.douyin.com/",
    }
    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=30.0) as client:
            resp = await client.get(cover_url)
            if resp.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                print(f"Saved cover to {output_path}")
                return True
    except Exception as e:
        print(f"Error downloading cover: {e}")
    return False

async def recover_videos():
    print("Initializing CrawlerService...")
    service = CrawlerService()
    mongodb = get_mongodb()
    
    # Query for missing videos
    query = {
        "platform": "douyin",
        "video_path": None,
    }
    
    cursor = mongodb.raw_data.find(query)
    all_items = list(cursor)
    
    valid_items = []
    for item in all_items:
        item_id = item.get("content_id") or item.get("aweme_id") or item.get("video_id")
        if item_id and str(item_id).isdigit() and len(str(item_id)) > 15:
            valid_items.append(item)
            
    print(f"Found {len(valid_items)} valid items to recover.")
    
    for index, item in enumerate(valid_items):
        item_id = str(item.get("content_id") or item.get("aweme_id") or item.get("video_id"))
        print(f"\n[{index+1}/{len(valid_items)}] Processing {item_id}...")
        
        target_url = f"https://www.douyin.com/video/{item_id}"
        
        try:
            # 1. Run MediaCrawler to get metadata
            print("Starting crawl...")
            result = service.crawl_platform(
                platform="douyin",
                keywords=[], 
                crawl_type="detail",
                target_url=target_url,
                enable_media_download=False, # We download manually
                max_items=1
            )
            
            crawled_items = result.get("items", [])
            target_item = None
            
            if crawled_items:
                # Find the item that matches our ID
                for c_item in crawled_items:
                    c_id = str(c_item.get("aweme_id") or c_item.get("id") or c_item.get("video_id"))
                    if c_id == item_id:
                        target_item = c_item
                        break
                
                if not target_item:
                    print(f"WARNING: Crawled data does not contain requested ID {item_id}. Found IDs: {[c.get('aweme_id') for c in crawled_items]}")
            
            if target_item:
                # Extract video URL
                video_url = None
                if "video_download_url" in target_item:
                    video_url = target_item["video_download_url"]
                elif "video" in target_item and isinstance(target_item["video"], dict):
                    play_addr = target_item["video"].get("play_addr", {})
                    url_list = play_addr.get("url_list", [])
                    if url_list:
                        video_url = url_list[0]
                
                # Extract Cover URL
                cover_url = target_item.get("cover_url")
                if not cover_url and "video" in target_item:
                     cover_url = target_item["video"].get("cover", {}).get("url_list", [None])[0]

                # Prepare paths
                output_dir = service.data_dir / "douyin" / item_id
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # Download Video
                video_success = False
                if video_url:
                    video_path = output_dir / "video.mp4"
                    video_success = await download_video(video_url, video_path)
                else:
                    print("No video URL found")
                    
                # Download Cover
                if cover_url:
                    cover_path = output_dir / "cover.jpeg"
                    await download_cover(cover_url, cover_path)
                
                # Update DB
                update_fields = {
                    "raw_data": target_item, # Update with fresh metadata
                    "crawled_at": datetime.now()
                }
                
                if video_success:
                    update_fields["video_path"] = f"douyin/{item_id}/video.mp4"
                    update_fields["media_downloaded"] = True
                    
                if (output_dir / "cover.jpeg").exists():
                    update_fields["image_path"] = f"douyin/{item_id}/cover.jpeg"
                    
                mongodb.raw_data.update_one(
                    {"_id": item["_id"]},
                    {"$set": update_fields}
                )
                print("DB updated.")
                
            else:
                print("No data returned from crawler")
                
        except Exception as e:
            print(f"Failed to process {item_id}: {e}")
            
        # Sleep to be nice
        print("Sleeping for 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    from datetime import datetime
    asyncio.run(recover_videos())
