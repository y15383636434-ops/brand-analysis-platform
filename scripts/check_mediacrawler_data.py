import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings

def check_mediacrawler_data():
    print("=" * 50)
    print("MediaCrawler 数据目录检查")
    print("=" * 50)
    
    # 获取 MediaCrawler 路径
    mediacrawler_path = settings.MEDIACRAWLER_PATH
    if mediacrawler_path:
        if mediacrawler_path.startswith("./") or mediacrawler_path.startswith(".\\"):
            mediacrawler_path = (project_root / mediacrawler_path.lstrip("./\\")).resolve()
        else:
            mediacrawler_path = Path(mediacrawler_path)
            
    print(f"MediaCrawler 路径: {mediacrawler_path}")
    
    if not mediacrawler_path or not mediacrawler_path.exists():
        print("MediaCrawler 路径不存在")
        return

    data_dir = mediacrawler_path / "data"
    print(f"数据目录: {data_dir}")
    
    if data_dir.exists():
        json_files = list(data_dir.rglob("*.json"))
        print(f"JSON 文件总数: {len(json_files)}")
        
        # 查找最近 24 小时内的文件
        recent_files = []
        now = datetime.now().timestamp()
        for f in json_files:
            mtime = f.stat().st_mtime
            if now - mtime < 24 * 3600:
                recent_files.append(f)
        
        print(f"最近 24 小时内的文件数: {len(recent_files)}")
        
        if recent_files:
            print("\n最近的文件列表:")
            for f in sorted(recent_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                 print(f"  - {f.name} ({datetime.fromtimestamp(f.stat().st_mtime)})")
        elif json_files:
             print("\n最新文件（超过24小时）:")
             latest = max(json_files, key=lambda f: f.stat().st_mtime)
             print(f"  - {latest.name} ({datetime.fromtimestamp(latest.stat().st_mtime)})")
    else:
        print("MediaCrawler/data 目录不存在")

if __name__ == "__main__":
    check_mediacrawler_data()
