import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.media_downloader import media_downloader
from loguru import logger

async def test_download():
    # ID from the log that failed with 403
    item_id = "7412191770093686067" 
    platform = "douyin"
    
    print(f"Testing download for {platform} item {item_id}...")
    
    # Try to download using our service
    # This will first try to fetch info from API since we don't provide a URL
    result = await media_downloader.download_item_media(platform, item_id)
    
    print(f"Download result: {result}")
    
    if result.get("success"):
        print(f"File saved to: {result.get('path')}")
        # Verify file exists
        if os.path.exists(result.get('path')):
            print("File verification: SUCCESS")
            size = os.path.getsize(result.get('path'))
            print(f"File size: {size} bytes")
        else:
            print("File verification: FAILED (File not found)")
    else:
        print("Download failed.")

if __name__ == "__main__":
    asyncio.run(test_download())
