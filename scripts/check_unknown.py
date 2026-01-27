import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_mongodb

def check_unknown_platform():
    mongodb = get_mongodb()
    cursor = mongodb.raw_data.find({"platform": "unknown"})
    items = list(cursor)
    print(f"Found {len(items)} items with platform 'unknown'")
    for item in items[:5]:
        print(f"ID: {item.get('_id')}, Title: {item.get('title')}, Content ID: {item.get('content_id')}")

if __name__ == "__main__":
    check_unknown_platform()
