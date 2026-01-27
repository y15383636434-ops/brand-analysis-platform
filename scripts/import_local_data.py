import sys
import os
from pathlib import Path
import json
from datetime import datetime
import hashlib
from pymongo import MongoClient

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from loguru import logger

def import_local_data():
    print("=" * 50)
    print("导入本地数据到 MongoDB")
    print("=" * 50)
    
    # 1. 连接 MongoDB
    try:
        mongo_client = MongoClient(
            host=settings.MONGODB_HOST,
            port=settings.MONGODB_PORT,
            serverSelectionTimeoutMS=2000
        )
        db = mongo_client[settings.MONGODB_DATABASE]
        collection = db.raw_data
        print(f"MongoDB 连接成功: {settings.MONGODB_DATABASE}")
    except Exception as e:
        print(f"MongoDB 连接失败: {e}")
        return

    # 2. 获取 MediaCrawler 路径
    mediacrawler_path = settings.MEDIACRAWLER_PATH
    if mediacrawler_path:
        if mediacrawler_path.startswith("./") or mediacrawler_path.startswith(".\\"):
            mediacrawler_path = (project_root / mediacrawler_path.lstrip("./\\")).resolve()
        else:
            mediacrawler_path = Path(mediacrawler_path)
    
    if not mediacrawler_path or not mediacrawler_path.exists():
        print("MediaCrawler 路径不存在")
        return

    data_dir = mediacrawler_path / "data"
    print(f"扫描数据目录: {data_dir}")
    
    if not data_dir.exists():
        print("数据目录不存在")
        return

    # 3. 遍历 JSON 文件
    json_files = list(data_dir.rglob("*.json"))
    print(f"发现 {len(json_files)} 个 JSON 文件")
    
    imported_count = 0
    skipped_count = 0
    
    for file_path in json_files:
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
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                if "items" in data:
                    items = data["items"]
                else:
                    items = [data]
            
            # 过滤掉非内容数据（如 config.json 等）
            real_items = [item for item in items if isinstance(item, dict) and (item.get("id") or item.get("title") or item.get("content"))]
            
            if not real_items:
                continue
                
            print(f"正在导入 {file_path.name} ({len(real_items)} 条数据)...")
            
            for item in real_items:
                # 构建文档
                content_id = item.get("id", "")
                title = item.get("title", "")
                content = item.get("content", "")
                
                if not content_id:
                     # 使用title+content的前100字符生成唯一标识
                    unique_str = f"{title}{content[:100]}"
                    content_id = hashlib.md5(unique_str.encode()).hexdigest()
                
                doc = {
                    "platform": platform,
                    "content_id": content_id,
                    "title": title,
                    "content": content,
                    "raw_data": item,
                    "imported_at": datetime.now(),
                    "source_file": str(file_path.name)
                }
                
                # 检查是否存在
                existing = collection.find_one({
                    "content_id": content_id,
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
    print(f"新增: {imported_count}")
    print(f"跳过 (已存在): {skipped_count}")
    print("=" * 50)

if __name__ == "__main__":
    import_local_data()
