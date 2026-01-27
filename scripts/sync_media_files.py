"""
同步 MediaCrawler 下载的媒体文件到项目数据目录
"""
import os
import sys
import shutil
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import settings

def sync_media_files():
    """同步媒体文件"""
    print("=" * 60)
    print("开始同步媒体文件")
    print("=" * 60)
    
    # 1. 确定源目录和目标目录
    if not settings.MEDIACRAWLER_PATH:
        print("错误: 未配置 MEDIACRAWLER_PATH")
        return
        
    mediacrawler_path = Path(settings.MEDIACRAWLER_PATH)
    if not mediacrawler_path.is_absolute():
        mediacrawler_path = (project_root / settings.MEDIACRAWLER_PATH).resolve()
        
    source_dir = mediacrawler_path / "data" / "crawled_data"
    target_dir = settings.DATA_DIR / "crawled_data"
    
    if not source_dir.exists():
        print(f"错误: MediaCrawler 数据目录不存在: {source_dir}")
        return
        
    print(f"源目录: {source_dir}")
    print(f"目标目录: {target_dir}")
    
    # 2. 遍历源目录
    # 结构: platform/content_id/files
    platforms = [d for d in source_dir.iterdir() if d.is_dir()]
    
    total_copied = 0
    total_skipped = 0
    
    for platform_dir in platforms:
        platform_name = platform_dir.name
        print(f"\n正在处理平台: {platform_name}")
        
        content_dirs = [d for d in platform_dir.iterdir() if d.is_dir()]
        print(f"发现 {len(content_dirs)} 个内容目录")
        
        for content_dir in content_dirs:
            content_id = content_dir.name
            
            # 构建目标目录
            target_content_dir = target_dir / platform_name / content_id
            target_content_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            for file_path in content_dir.iterdir():
                if file_path.is_file():
                    target_file = target_content_dir / file_path.name
                    
                    should_copy = False
                    if not target_file.exists():
                        should_copy = True
                    elif target_file.stat().st_size != file_path.stat().st_size:
                        should_copy = True
                        
                    if should_copy:
                        try:
                            shutil.copy2(file_path, target_file)
                            # print(f"已复制: {file_path.name}")
                            total_copied += 1
                        except Exception as e:
                            print(f"复制失败 {file_path}: {e}")
                    else:
                        total_skipped += 1
                        
    print("\n" + "=" * 60)
    print(f"同步完成")
    print(f"复制文件数: {total_copied}")
    print(f"跳过文件数: {total_skipped}")
    print("=" * 60)

if __name__ == "__main__":
    sync_media_files()
