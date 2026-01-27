import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings

def update_crawl_tasks_table():
    mysql_url = (
        f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
        f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
        f"?charset=utf8mb4"
    )
    engine = create_engine(mysql_url)

    try:
        with engine.connect() as conn:
            print(f"Connecting to {settings.MYSQL_DATABASE}...")
            
            # Add crawl_type column
            try:
                conn.execute(text("ALTER TABLE crawl_tasks ADD COLUMN crawl_type VARCHAR(20) DEFAULT 'search' COMMENT '爬取类型: search/creator'"))
                print("Added column: crawl_type")
            except Exception as e:
                print(f"Column crawl_type might already exist: {e}")
                
            # Add target_url column
            try:
                conn.execute(text("ALTER TABLE crawl_tasks ADD COLUMN target_url TEXT COMMENT '目标链接(博主主页/视频链接)'"))
                print("Added column: target_url")
            except Exception as e:
                print(f"Column target_url might already exist: {e}")
                
            conn.commit()
            print("Table crawl_tasks updated successfully.")
            
    except Exception as e:
        print(f"Error updating table: {e}")

if __name__ == "__main__":
    update_crawl_tasks_table()
