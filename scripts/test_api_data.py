import sys
import os
import asyncio
import httpx
import json
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from app.models.brand import Brand

def get_brand_id():
    db = next(get_db())
    brand = db.query(Brand).first()
    if brand:
        return brand.id
    return 1

async def test_api_response():
    brand_id = get_brand_id()
    print(f"Testing API for brand_id: {brand_id}")
    
    async with httpx.AsyncClient() as client:
        url = f"http://localhost:8000/api/v1/brands/{brand_id}/data?page=1&page_size=10"
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("data", {}).get("items", [])
                print(f"Got {len(items)} items from API.")
                for i, item in enumerate(items):
                    print(f"[{i+1}] ID: {item.get('content_id')}")
                    print(f"    Video Path: {item.get('video_path')}")
            else:
                print(f"API Error: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_response())
