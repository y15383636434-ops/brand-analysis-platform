"""
环境检查脚本
"""
import sys
from pathlib import Path

def check_environment():
    """检查开发环境"""
    print("=" * 50)
    print("环境检查")
    print("=" * 50)
    
    # 检查Python版本
    print(f"\n[OK] Python版本: {sys.version}")
    
    # 检查必要的包
    required_packages = [
        "fastapi",
        "sqlalchemy",
        "pymysql",
        "pymongo",
        "redis",
        "pandas",
        "pydantic"
    ]
    
    print("\n检查必要的Python包:")
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"  [OK] {package}")
        except ImportError:
            print(f"  [X] {package} (未安装)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n缺少以下包，请运行: pip install -r requirements.txt")
        print(f"  缺少的包: {', '.join(missing_packages)}")
    else:
        print("\n[OK] 所有必要的包已安装")
    
    # 检查数据库连接
    print("\n检查数据库连接:")
    try:
        from config import settings
        from sqlalchemy import create_engine, text
        
        # 检查MySQL
        try:
            mysql_url = (
                f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
                f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
            )
            engine = create_engine(mysql_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"  [OK] MySQL连接成功 ({settings.MYSQL_HOST}:{settings.MYSQL_PORT})")
        except Exception as e:
            print(f"  [X] MySQL连接失败: {e}")
        
        # 检查MongoDB
        try:
            from pymongo import MongoClient
            client = MongoClient(settings.MONGODB_HOST, settings.MONGODB_PORT)
            client.admin.command('ping')
            print(f"  [OK] MongoDB连接成功 ({settings.MONGODB_HOST}:{settings.MONGODB_PORT})")
        except Exception as e:
            print(f"  [X] MongoDB连接失败: {e}")
        
        # 检查Redis
        try:
            from redis import Redis
            redis_client = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD
            )
            redis_client.ping()
            print(f"  [OK] Redis连接成功 ({settings.REDIS_HOST}:{settings.REDIS_PORT})")
        except Exception as e:
            print(f"  [X] Redis连接失败: {e}")
    
    except Exception as e:
        print(f"  [X] 配置加载失败: {e}")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    check_environment()

