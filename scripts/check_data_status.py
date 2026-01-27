import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from pymongo import MongoClient
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings

def check_data_status():
    print("=" * 50)
    print("数据状态检查报告")
    print("=" * 50)
    
    # 1. 检查 MySQL 数据
    print("\n[1] MySQL 数据库检查")
    try:
        mysql_url = (
            f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
            f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
            f"?charset=utf8mb4"
        )
        engine = create_engine(mysql_url)
        with engine.connect() as conn:
            # 检查 brands 表
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM brands"))
                brand_count = result.scalar()
                print(f"  - brands 表记录数: {brand_count}")
            except Exception as e:
                print(f"  - brands 表查询失败: {e}")

            # 检查 crawl_tasks 表
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM crawl_tasks"))
                task_count = result.scalar()
                print(f"  - crawl_tasks 表记录数: {task_count}")
            except Exception as e:
                print(f"  - crawl_tasks 表查询失败: {e}")
                
            # 检查 analysis_tasks 表
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM analysis_tasks"))
                analysis_count = result.scalar()
                print(f"  - analysis_tasks 表记录数: {analysis_count}")
            except Exception as e:
                print(f"  - analysis_tasks 表查询失败: {e}")

    except Exception as e:
        print(f"  - MySQL 连接失败: {e}")

    # 2. 检查 MongoDB 数据
    print("\n[2] MongoDB 数据库检查")
    try:
        mongo_client = MongoClient(
            host=settings.MONGODB_HOST,
            port=settings.MONGODB_PORT,
            serverSelectionTimeoutMS=2000
        )
        # 尝试连接
        mongo_client.admin.command('ping')
        
        db = mongo_client[settings.MONGODB_DATABASE]
        
        # 检查 raw_data 集合
        raw_data_count = db.raw_data.count_documents({})
        print(f"  - raw_data 集合文档数: {raw_data_count}")
        
        if raw_data_count > 0:
            latest = db.raw_data.find_one(sort=[("crawled_at", -1)])
            print(f"  - 最新数据时间: {latest.get('crawled_at')}")

    except Exception as e:
        print(f"  - MongoDB 连接或查询失败: {e}")

    # 3. 检查本地文件数据
    print("\n[3] 本地数据文件检查")
    data_dir = settings.DATA_DIR / "crawled_data"
    if data_dir.exists():
        json_files = list(data_dir.rglob("*.json"))
        print(f"  - JSON 文件总数: {len(json_files)}")
        if json_files:
            # 按修改时间排序
            latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
            print(f"  - 最新文件: {latest_file}")
            print(f"  - 修改时间: {datetime.fromtimestamp(latest_file.stat().st_mtime)}")
    else:
        print(f"  - 数据目录 {data_dir} 不存在")

    # 4. 检查日志中的错误
    print("\n[4] 最近日志检查 (最后 20 行)")
    log_file = Path(settings.LOG_FILE)
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-20:]:
                    print(f"  {line.strip()}")
        except Exception as e:
            print(f"  - 读取日志失败: {e}")
    else:
        print(f"  - 日志文件 {log_file} 不存在")

    print("\n" + "=" * 50)

if __name__ == "__main__":
    from datetime import datetime
    check_data_status()
