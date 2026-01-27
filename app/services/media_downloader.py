import httpx
import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from loguru import logger
import asyncio

from config import settings
from app.services.crawler_service import CrawlerService

# Headers for Douyin requests
DOUYIN_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Referer": "https://www.douyin.com/",
}

class DouyinDownloader:
    """Douyin Video Downloader based on MediaCrawlerPro logic"""
    
    def __init__(self):
        self.timeout = 10
    
    def _extract_video_url(self, video_item: Dict) -> str:
        """Extract video URL from video item dictionary"""
        # Logic from MediaCrawlerPro-Downloader-main/.../extractor.py
        url_h264_list = video_item.get("play_addr_h264", {}).get("url_list", [])
        url_256_list = video_item.get("play_addr_256", {}).get("url_list", [])
        url_list = video_item.get("play_addr", {}).get("url_list", [])
        
        # Priority: H264 > 256 > Normal
        actual_url_list = url_h264_list or url_256_list or url_list
        
        if not actual_url_list:
            return ""
            
        # Usually the last one is the best or most accessible? 
        # MediaCrawlerPro uses index 1 if available, otherwise 0?
        # actual_url_list[1] in the reference code. 
        # Let's try to get the longest URL (often contains more tokens) or just the last one.
        # But reference said [1]. Let's be safe and try to find a valid one.
        
        for url in reversed(actual_url_list):
            if url: 
                return url
                
        return actual_url_list[-1] if actual_url_list else ""

    async def get_video_info(self, item_id: str) -> Optional[Dict]:
        """Fetch video info from Douyin API (Public Endpoint)"""
        # Note: This endpoint might require signatures (X-Bogus) for some requests.
        # But detailed pages sometimes work with just headers or cached cookies.
        # If this fails, we might need to rely on the data already in MongoDB if available.
        
        url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={item_id}"
        
        async with httpx.AsyncClient(headers=DOUYIN_HEADERS, timeout=self.timeout, follow_redirects=True) as client:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("aweme_detail")
            except Exception as e:
                logger.error(f"Failed to fetch video info for {item_id}: {e}")
                return None
        return None

    async def download_video(self, url: str, save_path: Path) -> bool:
        """Download video from URL to path"""
        if not url:
            return False
            
        if save_path.exists() and save_path.stat().st_size > 0:
            logger.info(f"Video already exists at {save_path}")
            return True
            
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Try with headers first
        success = await self._download_with_headers(url, save_path, DOUYIN_HEADERS)
        if success:
            return True
            
        # Retry without headers (sometimes Referer causes 403)
        logger.info(f"Retrying download without headers for {url}")
        success = await self._download_with_headers(url, save_path, {})
        if success:
            return True
            
        # Retry with User-Agent only
        logger.info(f"Retrying download with User-Agent only for {url}")
        ua_headers = {"User-Agent": DOUYIN_HEADERS["User-Agent"]}
        return await self._download_with_headers(url, save_path, ua_headers)

    async def _download_with_headers(self, url: str, save_path: Path, headers: Dict) -> bool:
        async with httpx.AsyncClient(headers=headers, timeout=30, follow_redirects=True) as client:
            try:
                async with client.stream('GET', url) as response:
                    if response.status_code != 200:
                        logger.error(f"Download failed with status {response.status_code}")
                        return False
                        
                    with open(save_path, 'wb') as f:
                        async for chunk in response.aiter_bytes():
                            f.write(chunk)
                return True
            except Exception as e:
                logger.error(f"Download error: {e}")
                # Cleanup partial file
                if save_path.exists():
                    save_path.unlink()
                return False

class MediaDownloader:
    """Unified Media Downloader Service"""
    
    def __init__(self):
        self.douyin = DouyinDownloader()
        self.crawler_service = CrawlerService()
        
    async def download_item_media(self, platform: str, item_id: str, video_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Download media for a specific item.
        If video_url is provided, use it. Otherwise try to fetch it.
        If direct download fails, fallback to MediaCrawler.
        """
        result = {"success": False, "message": ""}
        
        # Determine paths
        # Structure: data/crawled_data/{platform}/{item_id}/video.mp4
        platform_code = platform.lower()
        if platform_code == "dy": platform_code = "douyin"
        if platform_code == "wb": platform_code = "weibo"
        
        base_dir = settings.DATA_DIR / "crawled_data" / platform_code / item_id
        video_path = base_dir / "video.mp4"
        
        # 1. If video_url is provided (e.g. from database)
        if video_url:
            success = await self.douyin.download_video(video_url, video_path)
            if success:
                return {"success": True, "path": str(video_path), "source": "provided_url"}
        
        # 2. If no URL or download failed, try to fetch info (Direct API)
        if platform_code == "douyin":
            info = await self.douyin.get_video_info(item_id)
            if info:
                # Try to extract URL from fetched info
                extracted_url = self.douyin._extract_video_url(info.get("video", {}))
                if extracted_url:
                    success = await self.douyin.download_video(extracted_url, video_path)
                    if success:
                        return {"success": True, "path": str(video_path), "source": "fetched_info"}
        
        # 3. Fallback: Use MediaCrawler (Detail Mode)
        logger.info(f"Direct download failed for {item_id}, falling back to MediaCrawler...")
        return await self._download_via_crawler(platform, item_id)

    async def _download_via_crawler(self, platform: str, item_id: str) -> Dict[str, Any]:
        """Use MediaCrawler to download media"""
        # Construct URL
        target_url = self._get_detail_url(platform, item_id)
        if not target_url:
             return {"success": False, "message": f"Unknown platform or URL format for {platform}"}

        # Run crawler in thread executor because it's blocking
        loop = asyncio.get_running_loop()
        try:
             # We use a lambda to call the synchronous method
             # Note: crawl_platform might print to stdout, which is fine
             logger.info(f"Starting MediaCrawler for {target_url}")
             
             # Use run_in_executor to avoid blocking the event loop
             # MediaCrawler will download files to its own data directory
             crawl_result = await loop.run_in_executor(
                 None, 
                 lambda: self.crawler_service.crawl_platform(
                     platform=platform,
                     keywords=[],
                     crawl_type="detail",
                     target_url=target_url,
                     enable_media_download=True
                 )
             )
             
             # After crawl, we need to find and move the file
             # CrawlerService.save_crawled_data has logic for this, but it requires DB interaction
             # Here we just want the file path.
             
             # Check if file exists in project dir (CrawlerService.save_crawled_data might have been called if we integrated it there? 
             # No, crawl_platform returns result, save_crawled_data is separate)
             
             # So we need to manually move the file like save_crawled_data does
             path = self._move_downloaded_file(platform, item_id)
             
             if path:
                 return {"success": True, "path": str(path), "source": "crawler_fallback"}
             else:
                 return {"success": False, "message": "Crawler finished but file not found in expected location"}
                 
        except Exception as e:
             logger.error(f"Crawler fallback failed: {e}")
             return {"success": False, "message": str(e)}

    def _get_detail_url(self, platform: str, item_id: str) -> str:
        """Construct detail URL for platform"""
        p = platform.lower()
        if p in ["dy", "douyin"]:
            return f"https://www.douyin.com/video/{item_id}"
        elif p in ["xhs"]:
            return f"https://www.xiaohongshu.com/explore/{item_id}"
        elif p in ["wb", "weibo"]:
            # Weibo ID might need conversion or just use detail link if ID is mid
            return f"https://weibo.com/detail/{item_id}"
        elif p in ["bili", "bilibili"]:
            return f"https://www.bilibili.com/video/{item_id}"
        return ""

    def _move_downloaded_file(self, platform: str, item_id: str) -> Optional[Path]:
        """Move file from MediaCrawler dir to Project dir"""
        if not self.crawler_service.mediacrawler_path:
            return None
            
        platform_code = platform.lower()
        if platform_code == "dy": platform_code = "douyin"
        if platform_code == "wb": platform_code = "weibo"
        if platform_code == "xhs": platform_code = "xhs" # MediaCrawler uses 'xhs' folder?
        
        # MediaCrawler path: data/crawled_data/{platform}/{item_id}/video.mp4
        mc_data_path = self.crawler_service.mediacrawler_path / "data/crawled_data" / platform_code / str(item_id)
        
        # Target path
        target_base_path = settings.DATA_DIR / "crawled_data" / platform_code / str(item_id)
        target_base_path.mkdir(parents=True, exist_ok=True)
        
        video_path = None
        
        if mc_data_path.exists():
            # Video
            mc_video = mc_data_path / "video.mp4"
            if mc_video.exists():
                target_video = target_base_path / "video.mp4"
                if not target_video.exists() or target_video.stat().st_size != mc_video.stat().st_size:
                    try:
                        shutil.copy2(mc_video, target_video)
                        logger.info(f"Copied video to {target_video}")
                    except Exception as e:
                        logger.warning(f"Failed to copy video: {e}")
                
                if target_video.exists():
                    video_path = target_video

            # Images (Optional, copy if exists)
            for img_file in mc_data_path.glob("*.jpeg"):
                 target_img = target_base_path / img_file.name
                 if not target_img.exists():
                     try:
                         shutil.copy2(img_file, target_img)
                     except:
                         pass

        return video_path

media_downloader = MediaDownloader()
