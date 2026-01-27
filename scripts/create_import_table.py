import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, text

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings

def create_import_table():
    mysql_url = (
        f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
        f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
        f"?charset=utf8mb4"
    )
    engine = create_engine(mysql_url)

    try:
        with engine.connect() as conn:
            print(f"Connecting to {settings.MYSQL_DATABASE}...")
            
            # Create table SQL
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS data_import_tasks (
                id INTEGER NOT NULL AUTO_INCREMENT, 
                brand_id INTEGER NOT NULL, 
                celery_task_id VARCHAR(50), 
                status ENUM('pending','running','completed','failed','cancelled'), 
                file_list JSON, 
                total_files INTEGER DEFAULT 0, 
                processed_files INTEGER DEFAULT 0, 
                imported_items INTEGER DEFAULT 0, 
                skipped_items INTEGER DEFAULT 0, 
                error_message TEXT, 
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
                started_at DATETIME, 
                completed_at DATETIME, 
                PRIMARY KEY (id), 
                KEY ix_data_import_tasks_id (id), 
                KEY ix_data_import_tasks_brand_id (brand_id), 
                KEY ix_data_import_tasks_celery_task_id (celery_task_id), 
                KEY ix_data_import_tasks_status (status), 
                KEY ix_data_import_tasks_created_at (created_at), 
                CONSTRAINT fk_data_import_tasks_brand_id FOREIGN KEY(brand_id) REFERENCES brands (id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            print("Executing CREATE TABLE...")
            conn.execute(text(create_table_sql))
            conn.commit()
            print("Table data_import_tasks created successfully (or already exists).")
            
    except Exception as e:
        print(f"Error creating table: {e}")

if __name__ == "__main__":
    create_import_table()
