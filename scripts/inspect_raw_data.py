import sys
import os
import asyncio
import json
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_mongodb

def inspect_data():
    mongodb = get_mongodb()
    item_id = "7597669042429638053"
    
    item = mongodb.raw_data.find_one({"$or": [{"content_id": item_id}, {"aweme_id": item_id}]})
    
    if item:
        print(f"Found item {item_id}")
        print("Document Keys:", list(item.keys()))
        print(f"Video Path in DB: {item.get('video_path')}")
        print(f"Image Path in DB: {item.get('image_path')}")
        
        raw = item.get("raw_data", {})
        print("Raw Data Keys:", list(raw.keys()))
        
        if "video" in raw:
            print("Video Info Keys:", list(raw["video"].keys()))
            if "play_addr" in raw["video"]:
                print("Play Addr Keys:", list(raw["video"]["play_addr"].keys()))
                print("URL List:", raw["video"]["play_addr"].get("url_list"))
        else:
            print("No 'video' key in raw_data")
            
        # Check other potential locations
        if "video_download_url" in raw:
             print(f"Found video_download_url: {raw['video_download_url']}")
             
    else:
        print(f"Item {item_id} not found in DB")

if __name__ == "__main__":
    inspect_data()
