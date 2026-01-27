import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, text

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings

def update_crawl_task_table():
    mysql_url = (
        f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
        f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
        f"?charset=utf8mb4"
    )
    engine = create_engine(mysql_url)

    try:
        with engine.connect() as conn:
            print(f"Connecting to {settings.MYSQL_DATABASE}...")
            
            # Check if columns exist
            result = conn.execute(text("SHOW COLUMNS FROM crawl_tasks LIKE 'crawl_type'"))
            if not result.fetchone():
                print("Adding crawl_type column...")
                conn.execute(text("ALTER TABLE crawl_tasks ADD COLUMN crawl_type ENUM('search','creator','detail') DEFAULT 'search' COMMENT '爬取类型' AFTER platform"))
            else:
                print("Column crawl_type already exists.")
                
            result = conn.execute(text("SHOW COLUMNS FROM crawl_tasks LIKE 'target_url'"))
            if not result.fetchone():
                print("Adding target_url column...")
                conn.execute(text("ALTER TABLE crawl_tasks ADD COLUMN target_url TEXT COMMENT '目标链接' AFTER keyword"))
            else:
                print("Column target_url already exists.")
                
            conn.commit()
            print("Table crawl_tasks updated successfully.")
            
    except Exception as e:
        print(f"Error updating table: {e}")

if __name__ == "__main__":
    update_crawl_task_table()
