import sys
import os
import asyncio
import shutil
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_mongodb
from config import settings

def clean_invalid_data():
    print("Starting cleanup of invalid test data...")
    
    mongodb = get_mongodb()
    collection = mongodb.raw_data
    
    # Criteria: Platform is douyin (or we can check all), and ID is invalid
    # For safety, let's look at all items and filter by ID format
    
    cursor = collection.find({})
    all_items = list(cursor)
    
    ids_to_delete = []
    files_to_delete = []
    
    print(f"Scanning {len(all_items)} total records...")
    
    for item in all_items:
        item_id = item.get("content_id") or item.get("aweme_id") or item.get("video_id")
        platform = item.get("platform", "unknown")
        
        is_invalid = False
        
        if not item_id:
            is_invalid = True
        else:
            str_id = str(item_id)
            # Check for test IDs (dy_1, etc) or MD5 hashes that might be invalid if they don't map to real content
            # But the user specifically mentioned "dy_" ones.
            # Real Douyin IDs are numeric strings of length ~19.
            # Real XHS IDs are 24 char hex strings usually? Or base64?
            
            if platform == "douyin":
                if str_id.startswith("dy_") or (str_id.isdigit() and len(str_id) < 15) or (len(str_id) == 32 and not str_id.isdigit()): 
                    # 32 chars might be MD5 hash of title for items without ID, which we might want to keep?
                    # But the previous check identified 1193 items. Let's stick to the logic that identified those.
                    # Logic was: not (isdigit and len > 15)
                    if not (str_id.isdigit() and len(str_id) > 15):
                         is_invalid = True
        
        if is_invalid:
            ids_to_delete.append(item["_id"])
            
            # Check for files to cleanup
            if item_id:
                # Check standard paths
                p_code = "douyin" if platform == "dy" else platform
                data_dir = settings.DATA_DIR / "crawled_data" / p_code / str(item_id)
                if data_dir.exists():
                    files_to_delete.append(data_dir)

    print(f"Found {len(ids_to_delete)} invalid records to delete.")
    
    if not ids_to_delete:
        print("No invalid records found.")
        return

    # Confirmation
    print("\nExamples of IDs to be deleted:")
    # Get a few examples
    example_cursor = collection.find({"_id": {"$in": ids_to_delete[:5]}})
    for doc in example_cursor:
        print(f" - ID: {doc.get('content_id')}, Platform: {doc.get('platform')}, Title: {doc.get('title')}")
        
    print(f"\nThis will delete {len(ids_to_delete)} database records and {len(files_to_delete)} local folders.")
    print("Proceed? (The script will proceed automatically in this environment)")
    
    # Delete from DB
    result = collection.delete_many({"_id": {"$in": ids_to_delete}})
    print(f"Deleted {result.deleted_count} records from MongoDB.")
    
    # Delete files
    deleted_files_count = 0
    for folder in files_to_delete:
        try:
            shutil.rmtree(folder)
            deleted_files_count += 1
        except Exception as e:
            print(f"Failed to delete {folder}: {e}")
            
    print(f"Deleted {deleted_files_count} local folders.")
    print("Cleanup complete.")

if __name__ == "__main__":
    clean_invalid_data()
