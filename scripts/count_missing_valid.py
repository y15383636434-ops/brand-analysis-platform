import sys
import os
import asyncio
import re
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_mongodb

def count_valid_missing():
    mongodb = get_mongodb()
    
    # Query for missing videos
    query = {
        "platform": "douyin",
        "video_path": None,
        # "raw_data": {"$exists": True} # Doesn't matter if raw_data exists, we want to re-crawl
    }
    
    cursor = mongodb.raw_data.find(query)
    all_items = list(cursor)
    
    valid_items = []
    fake_items = []
    
    for item in all_items:
        item_id = item.get("content_id") or item.get("aweme_id") or item.get("video_id")
        if not item_id:
            continue
            
        # Check if ID is numeric and long enough (Douyin IDs are usually 19 digits)
        if str(item_id).isdigit() and len(str(item_id)) > 15:
            valid_items.append(item)
        else:
            fake_items.append(item_id)
            
    print(f"Total missing items: {len(all_items)}")
    print(f"Valid numeric IDs (candidates for re-crawl): {len(valid_items)}")
    print(f"Fake/Short IDs (ignored): {len(fake_items)}")
    if fake_items:
        print(f"Example fake IDs: {fake_items[:5]}")

if __name__ == "__main__":
    count_valid_missing()
