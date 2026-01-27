import os
import sys
from pathlib import Path
from pymongo import MongoClient

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

def check_missing_media():
    print("正在检查媒体文件一致性...")
    
    # Connect to MongoDB
    client = MongoClient(settings.MONGODB_HOST, settings.MONGODB_PORT)
    db = client[settings.MONGODB_DATABASE]
    collection = db["raw_data"]
    
    # Define data directories
    data_dirs = []
    if settings.MEDIACRAWLER_PATH:
        mc_path = Path(settings.MEDIACRAWLER_PATH)
        if not mc_path.is_absolute():
            # config.py BASE_DIR is the project root (where config.py is)
            mc_path = (settings.BASE_DIR / settings.MEDIACRAWLER_PATH).resolve()
        data_dirs.append(mc_path / "data" / "crawled_data")
        
    data_dirs.append(settings.DATA_DIR / "crawled_data")
    
    print(f"检查目录: {[str(d) for d in data_dirs]}")
    
    missing_count = 0
    total_checked = 0
    
    # Find documents with video or images
    # Check douyin first as per error
    platforms = collection.distinct("platform")
    print(f"Available platforms in DB: {platforms}")
    
    cursor = collection.find({"raw_data.aweme_id": {"$exists": True}}).limit(1)
    try:
        first_doc = next(cursor)
        print("\n[Real Data Sample]")
        print("Sample Douyin doc keys:", list(first_doc.keys()))
        if "raw_data" in first_doc:
             raw = first_doc["raw_data"]
             print(f"Raw data keys: {list(raw.keys())}")
             if "video" in raw:
                 print(f"Video info keys: {list(raw['video'].keys())}")
                 if "play_addr" in raw['video']:
                      print(f"Play addr: {raw['video']['play_addr']}")
             elif "video_url" in raw:
                  print(f"Video URL: {raw['video_url']}")
    except StopIteration:
        print("\nNo Douyin docs with raw_data.aweme_id found")

    cursor = collection.find({"platform": "douyin"})
    
    for doc in cursor:
        item_id = doc.get("content_id") or doc.get("aweme_id") or doc.get("video_id") or doc.get("note_id") or doc.get("id")
        if not item_id:
            continue
            
        platform = doc.get("platform", "douyin")
        total_checked += 1
        
        # Check for video
        # Default filename structure seems to be {platform}/{item_id}/video.mp4 based on 404
        
        # Construct expected paths
        found = False
        for data_dir in data_dirs:
            video_path = data_dir / platform / str(item_id) / "video.mp4"
            if video_path.exists():
                found = True
                break
        
        if not found and total_checked <= 20: # Limit detailed output
             print(f"[缺失] ID: {item_id} - 找不到 video.mp4")
             missing_count += 1
        elif not found:
             missing_count += 1

    # Specific check for the user reported ID
    target_id_str = "7443044715886316860"
    target_id_int = 7443044715886316860
    
    target_doc = collection.find_one({"$or": [
        {"content_id": target_id_str},
        {"aweme_id": target_id_str},
        {"video_id": target_id_str},
        {"note_id": target_id_str},
        {"raw_data.aweme_id": target_id_str},
        {"content_id": target_id_int},
        {"aweme_id": target_id_int},
        {"video_id": target_id_int},
        {"note_id": target_id_int},
        {"raw_data.aweme_id": target_id_int}
    ]})
    
    if target_doc:
        print(f"\n[已找到目标记录] ID: {target_id_str}")
        print(f"  Content ID: {target_doc.get('content_id')}")
        
        # Check raw_data structure
        raw_data = target_doc.get("raw_data", {})
        video_info = raw_data.get("video", {})
        play_addr = video_info.get("play_addr", {})
        url_list = play_addr.get("url_list", [])
        print(f"  Raw Video URL List Len: {len(url_list)}")
        if url_list:
            print(f"  Sample URL: {url_list[0][:50]}...")
            
        # Check file
        print(f"  Content ID: {target_doc.get('content_id')}")
        print(f"  Platform: {target_doc.get('platform')}")
        # Check file
        found = False
        platform = target_doc.get("platform", "douyin")
        c_id = target_doc.get("content_id")
        for data_dir in data_dirs:
            video_path = data_dir / platform / str(c_id) / "video.mp4"
            print(f"  Checking: {video_path} -> {video_path.exists()}")
            if video_path.exists():
                found = True
    else:
        print(f"\n[未找到目标记录] ID: {target_id_str} 在数据库中不存在")

    print(f"\n检查完成.")
    print(f"总共检查: {total_checked}")
    print(f"缺失文件: {missing_count}")

if __name__ == "__main__":
    check_missing_media()
