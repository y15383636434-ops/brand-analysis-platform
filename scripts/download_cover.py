import sys
import os
import asyncio
import httpx
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_mongodb
from config import settings

async def download_cover():
    item_id = "7597669042429638053"
    mongodb = get_mongodb()
    
    item = mongodb.raw_data.find_one({"$or": [{"content_id": item_id}, {"aweme_id": item_id}]})
    
    if not item:
        print("Item not found")
        return

    raw = item.get("raw_data", {})
    cover_url = raw.get("cover_url")
    
    # Try to find cover in video info if not at top level
    if not cover_url and "video" in raw:
        cover_url = raw["video"].get("cover", {}).get("url_list", [None])[0]
        
    if not cover_url:
        print("No cover URL found")
        return
        
    print(f"Found cover URL: {cover_url}")
    
    # Path
    platform = "douyin"
    base_dir = settings.DATA_DIR / "crawled_data" / platform / item_id
    base_dir.mkdir(parents=True, exist_ok=True)
    cover_path = base_dir / "cover.jpeg"
    
    # Download
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Referer": "https://www.douyin.com/",
    }
    
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        try:
            resp = await client.get(cover_url)
            if resp.status_code == 200:
                with open(cover_path, "wb") as f:
                    f.write(resp.content)
                print(f"Saved cover to {cover_path}")
                
                # Update DB
                mongodb.raw_data.update_one(
                    {"_id": item["_id"]},
                    {"$set": {"image_path": f"{platform}/{item_id}/cover.jpeg"}}
                )
                print("Updated DB with image_path")
            else:
                print(f"Failed to download cover: {resp.status_code}")
        except Exception as e:
            print(f"Error downloading cover: {e}")

if __name__ == "__main__":
    asyncio.run(download_cover())
