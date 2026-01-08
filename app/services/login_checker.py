"""
登录状态检查器
检查各平台是否已登录，如果已登录则跳过登录步骤
"""
from pathlib import Path
from typing import Dict, Optional
from loguru import logger


class LoginChecker:
    """登录状态检查器"""
    
    def __init__(self, mediacrawler_path: Optional[str] = None):
        """
        初始化登录检查器
        
        Args:
            mediacrawler_path: MediaCrawler路径
        """
        if mediacrawler_path:
            self.mediacrawler_path = Path(mediacrawler_path)
        else:
            self.mediacrawler_path = Path("MediaCrawler")
        
        # 平台代码映射（MediaCrawler使用的平台代码）
        self.platform_code_map = {
            "xhs": "xhs",
            "douyin": "dy",
            "weibo": "wb",
            "zhihu": "zhihu",
            "bilibili": "bili",
            "kuaishou": "ks"
        }
    
    def check_login_status(self, platform: str) -> bool:
        """
        检查平台是否已登录
        
        Args:
            platform: 平台代码（xhs, douyin等）
            
        Returns:
            True表示已登录，False表示未登录
        """
        platform_code = self.platform_code_map.get(platform, platform)
        
        # 检查普通模式的登录目录
        user_data_dir = self.mediacrawler_path / "browser_data" / f"{platform_code}_user_data_dir"
        
        # 检查CDP模式的登录目录
        cdp_user_data_dir = self.mediacrawler_path / "browser_data" / f"cdp_{platform_code}_user_data_dir"
        
        # 如果目录存在且有内容，说明已登录
        has_normal_login = user_data_dir.exists() and any(user_data_dir.iterdir())
        has_cdp_login = cdp_user_data_dir.exists() and any(cdp_user_data_dir.iterdir())
        
        is_logged_in = has_normal_login or has_cdp_login
        
        if is_logged_in:
            logger.info(f"[LoginChecker] {platform} 已登录，将使用保存的登录状态")
        else:
            logger.info(f"[LoginChecker] {platform} 未登录，首次使用需要扫码登录")
        
        return is_logged_in
    
    def get_all_login_status(self) -> Dict[str, bool]:
        """
        获取所有平台的登录状态
        
        Returns:
            平台代码到登录状态的映射
        """
        platforms = ["xhs", "douyin", "weibo", "zhihu", "bilibili", "kuaishou"]
        return {
            platform: self.check_login_status(platform)
            for platform in platforms
        }
    
    def print_login_status(self):
        """打印所有平台的登录状态"""
        platform_names = {
            "xhs": "小红书",
            "douyin": "抖音",
            "weibo": "微博",
            "zhihu": "知乎",
            "bilibili": "B站",
            "kuaishou": "快手"
        }
        
        print("="*60)
        print("平台登录状态")
        print("="*60)
        
        status = self.get_all_login_status()
        for platform, is_logged_in in status.items():
            status_text = "[OK] 已登录" if is_logged_in else "[X] 未登录"
            print(f"{platform_names.get(platform, platform)}: {status_text}")
        
        print("="*60)
        print("提示:")
        print("1. 已登录的平台会自动使用保存的登录信息，无需再次扫码")
        print("2. 未登录的平台首次使用需要扫码登录")
        print("3. 登录信息保存在 MediaCrawler/browser_data/ 目录")
        print("="*60)







