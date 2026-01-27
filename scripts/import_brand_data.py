import sys
import os
from pathlib import Path
import json
from datetime import datetime
import hashlib
from pymongo import MongoClient
import argparse

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from loguru import logger

def import_brand_data(brand_id: int, platforms: list = None, keywords: list = None, files: list = None):
    """
    导入品牌数据
    :param brand_id: 品牌ID
    :param platforms: 平台列表
    :param keywords: 关键词列表
    :param files: 指定文件路径列表 (优先级最高)
    """
    print("=" * 50)
    print(f"导入数据到品牌 (ID: {brand_id})")
    
    # ... (连接数据库部分保持不变) ...
    # 1. 连接数据库
    brand_keywords = []
    try:
        # MySQL 连接 (用于验证品牌和获取关键词)
        from app.core.database import SessionLocal
        from app.models.brand import Brand
        db = SessionLocal()
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            print(f"品牌 ID {brand_id} 不存在")
            return
        print(f"目标品牌: {brand.name}")
        brand_keywords = brand.keywords or []
        
        # MongoDB 连接
        mongo_client = MongoClient(
            host=settings.MONGODB_HOST,
            port=settings.MONGODB_PORT,
            serverSelectionTimeoutMS=2000
        )
        mongodb = mongo_client[settings.MONGODB_DATABASE]
        collection = mongodb.raw_data
        print(f"MongoDB 连接成功: {settings.MONGODB_DATABASE}")
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return
    finally:
        if 'db' in locals():
            db.close()

    # 确定目标文件列表
    target_files = []
    
    if files:
        print(f"指定导入文件数: {len(files)}")
        for f in files:
            path = Path(f)
            if path.exists():
                target_files.append(path)
            else:
                print(f"警告: 文件不存在 {f}")
    else:
        # 如果没有指定具体文件，则扫描目录 (原有逻辑)
        if platforms:
            print(f"指定平台: {', '.join(platforms)}")
            
        target_keywords = keywords if keywords else brand_keywords
        print(f"过滤关键词: {target_keywords if target_keywords else '无 (匹配所有)'}")
        
        # ... (扫描目录逻辑) ...
        mediacrawler_path = settings.MEDIACRAWLER_PATH
        if mediacrawler_path:
            if mediacrawler_path.startswith("./") or mediacrawler_path.startswith(".\\"):
                mediacrawler_path = (project_root / mediacrawler_path.lstrip("./\\")).resolve()
            else:
                mediacrawler_path = Path(mediacrawler_path)
        
        scan_dirs = []
        if mediacrawler_path and mediacrawler_path.exists():
            scan_dirs.append(mediacrawler_path / "data")
            
        crawled_data_dir = project_root / "data" / "crawled_data"
        if crawled_data_dir.exists():
            scan_dirs.append(crawled_data_dir)
            
        for d in scan_dirs:
            if d.exists():
                target_files.extend(list(d.rglob("*.json")))

    print(f"待处理文件数: {len(target_files)}")
    print("=" * 50)
    
    imported_count = 0
    skipped_count = 0
    
    for file_path in target_files:
        try:
            # 简单的平台判断
            filename = file_path.name.lower()
            platform = "unknown"
            if "xhs" in filename: platform = "xhs"
            elif "douyin" in filename or "dy" in filename: platform = "douyin"
            elif "bili" in filename: platform = "bilibili"
            elif "weibo" in filename or "wb" in filename: platform = "weibo"
            elif "tieba" in filename: platform = "tieba"
            elif "zhihu" in filename: platform = "zhihu"
            elif "kuaishou" in filename or "ks" in filename: platform = "kuaishou"
            
            # 如果不是指定文件模式，应用过滤逻辑
            if not files:
                # 过滤平台
                if platforms and platform not in platforms:
                    continue
                
                # 过滤关键词
                if target_keywords:
                    is_relevant = False
                    for kw in target_keywords:
                        if kw.lower() in filename:
                            is_relevant = True
                            break
                    if not is_relevant:
                        continue

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                if "items" in data:
                    items = data["items"]
                elif "data" in data and isinstance(data["data"], list):
                    items = data["data"]
                else:
                    items = [data]
            
            # 过滤有效数据
            real_items = [item for item in items if isinstance(item, dict) and (item.get("id") or item.get("aweme_id") or item.get("title") or item.get("content") or item.get("desc"))]
            
            if not real_items:
                continue
                
            print(f"正在导入 {file_path.name} ({len(real_items)} 条数据)...")
            
            for item in real_items:
                # ... (原有导入逻辑保持不变) ...
                content_id = item.get("id") or item.get("aweme_id") or item.get("note_id") or ""
                title = item.get("title") or item.get("desc") or ""
                content = item.get("content") or item.get("desc") or item.get("text") or ""
                
                if not content_id:
                    unique_str = f"{title}{content[:100]}"
                    content_id = hashlib.md5(unique_str.encode()).hexdigest()
                
                doc = {
                    "brand_id": brand_id,
                    "platform": platform,
                    "content_id": str(content_id),
                    "title": title,
                    "content": content,
                    "raw_data": item,
                    "crawled_at": datetime.now(),
                    "source_file": str(file_path.name)
                }
                
                existing = collection.find_one({
                    "brand_id": brand_id,
                    "content_id": str(content_id),
                    "platform": platform
                })
                
                if not existing:
                    collection.insert_one(doc)
                    imported_count += 1
                else:
                    skipped_count += 1
                    
        except Exception as e:
            print(f"处理文件 {file_path.name} 失败: {e}")

    print("\n" + "=" * 50)
    print(f"导入完成！")
    print(f"新增关联: {imported_count}")
    print(f"跳过 (已存在): {skipped_count}")
    print("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="导入品牌数据")
    parser.add_argument("brand_id", type=int, help="品牌ID")
    parser.add_argument("--platforms", nargs="+", help="指定平台列表")
    parser.add_argument("--keywords", nargs="+", help="指定关键词列表")
    parser.add_argument("--files", nargs="+", help="指定文件路径列表")
    
    args = parser.parse_args()
    import_brand_data(args.brand_id, args.platforms, args.keywords, args.files)
