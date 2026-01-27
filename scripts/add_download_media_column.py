import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings

def add_download_media_column():
    mysql_url = (
        f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
        f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
        f"?charset=utf8mb4"
    )
    engine = create_engine(mysql_url)

    try:
        with engine.connect() as conn:
            print(f"Connecting to {settings.MYSQL_DATABASE}...")
            
            try:
                print("Adding download_media column...")
                conn.execute(text("ALTER TABLE crawl_tasks ADD COLUMN download_media TINYINT(1) DEFAULT 1 COMMENT '是否下载媒体' AFTER include_comments"))
                conn.commit()
                print("Column download_media added.")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print("Column download_media already exists.")
                elif "Unknown column 'include_comments'" in str(e):
                    # include_comments column might not exist if using older schema version, add after max_items
                    try:
                         conn.execute(text("ALTER TABLE crawl_tasks ADD COLUMN download_media TINYINT(1) DEFAULT 1 COMMENT '是否下载媒体' AFTER max_items"))
                         conn.commit()
                         print("Column download_media added (after max_items).")
                    except Exception as e2:
                        print(f"Error adding download_media: {e2}")
                else:
                    print(f"Error adding download_media: {e}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    add_download_media_column()
