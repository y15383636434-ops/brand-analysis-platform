import sys
import os
import asyncio
from pathlib import Path

# Add MediaCrawlerPro-Downloader-main/DownloadServer to sys.path
downloader_path = Path("MediaCrawlerPro-Downloader-main/DownloadServer").resolve()
sys.path.append(str(downloader_path))

try:
    from pkg.media_platform_api.douyin.client import DouYinApiClient
    print("Successfully imported DouYinApiClient")
except ImportError as e:
    print(f"Import failed: {e}")
    # Check dependencies
    try:
        import httpx
        print("httpx installed")
    except ImportError:
        print("httpx NOT installed")
    
    try:
        import tenacity
        print("tenacity installed")
    except ImportError:
        print("tenacity NOT installed")

async def test_fetch():
    client = DouYinApiClient()
    await client.async_initialize()
    print("Client initialized")
    
    video_id = "7443044715886316860"
    print(f"Fetching video {video_id}...")
    
    try:
        detail = await client.get_video_by_id(video_id)
        if detail:
            print("Successfully fetched detail")
            print(f"Detail keys: {list(detail.keys())}")
            
            video_info = detail.get("video", {})
            play_addr = video_info.get("play_addr", {})
            url_list = play_addr.get("url_list", [])
            
            if url_list:
                print(f"Found video URL: {url_list[0]}")
            else:
                print("No video URL found in detail")
        else:
            print("No detail returned")
            
    except Exception as e:
        print(f"Error fetching video: {e}")

if __name__ == "__main__":
    asyncio.run(test_fetch())
