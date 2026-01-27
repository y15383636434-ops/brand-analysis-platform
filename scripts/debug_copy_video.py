import sys
import os
import shutil
from pathlib import Path
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from app.services.crawler_service import CrawlerService

def debug_copy():
    print("Debugging video copy logic...")
    
    service = CrawlerService()
    if not service.mediacrawler_path:
        print("MediaCrawler path not found!")
        return

    # Target ID from the previous check
    item_id = "7597669042429638053"
    platform = "douyin"
    
    print(f"Target ID: {item_id}")
    print(f"Platform: {platform}")
    
    # Simulate logic in save_crawled_data
    platform_code = service.PLATFORM_MAP.get(platform.lower(), platform.lower())
    print(f"Mapped platform code: {platform_code}")
    
    if platform_code == "dy": platform_code = "douyin"
    if platform_code == "xhs": platform_code = "xhs"
    print(f"Final platform code: {platform_code}")
    
    # Source path
    mc_data_path = service.mediacrawler_path / "data/crawled_data" / platform_code / str(item_id)
    print(f"Source path (MC): {mc_data_path}")
    print(f"Source exists: {mc_data_path.exists()}")
    
    if mc_data_path.exists():
        print(f"Contents of source: {list(mc_data_path.iterdir())}")
    
    # Target path
    target_base_path = service.data_dir / platform_code / str(item_id)
    print(f"Target path (Project): {target_base_path}")
    print(f"Target exists: {target_base_path.exists()}")
    
    # Try copy
    if mc_data_path.exists():
        target_base_path.mkdir(parents=True, exist_ok=True)
        
        mc_video = mc_data_path / "video.mp4"
        print(f"Checking video file: {mc_video}")
        
        if mc_video.exists():
            target_video = target_base_path / "video.mp4"
            print(f"Target video file: {target_video}")
            
            try:
                print("Attempting copy...")
                shutil.copy2(mc_video, target_video)
                print("Copy successful!")
            except Exception as e:
                print(f"Copy failed: {e}")
        else:
            print("Source video file does not exist.")
    else:
        print("Source directory does not exist.")

if __name__ == "__main__":
    debug_copy()
