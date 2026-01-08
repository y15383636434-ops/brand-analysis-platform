"""
API配置检查工具
检查当前API的配置状态和路由信息
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from config import settings
from app.main import app
from loguru import logger


def check_api_routes():
    """检查所有注册的API路由"""
    print("\n" + "=" * 80)
    print("API路由检查")
    print("=" * 80)
    
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            for method in route.methods:
                if method != 'HEAD':  # 排除HEAD方法
                    routes.append({
                        'method': method,
                        'path': route.path,
                        'name': getattr(route, 'name', 'N/A'),
                        'tags': getattr(route, 'tags', [])
                    })
    
    # 按路径排序
    routes.sort(key=lambda x: x['path'])
    
    print(f"\n总共发现 {len(routes)} 个API端点\n")
    
    # 按标签分组显示
    tags_dict = {}
    for route in routes:
        tags = route['tags'] if route['tags'] else ['未分类']
        for tag in tags:
            if tag not in tags_dict:
                tags_dict[tag] = []
            tags_dict[tag].append(route)
    
    for tag, tag_routes in sorted(tags_dict.items()):
        print(f"\n【{tag}】")
        print("-" * 80)
        for route in tag_routes:
            method_color = {
                'GET': '\033[92m',      # 绿色
                'POST': '\033[94m',     # 蓝色
                'PUT': '\033[93m',      # 黄色
                'DELETE': '\033[91m',   # 红色
                'PATCH': '\033[95m'     # 紫色
            }.get(route['method'], '\033[0m')
            reset_color = '\033[0m'
            print(f"  {method_color}{route['method']:8}{reset_color} {route['path']}")
    
    return routes


def check_api_config():
    """检查API配置"""
    print("\n" + "=" * 80)
    print("API配置检查")
    print("=" * 80)
    
    print(f"\n基础配置:")
    print(f"  项目名称: {settings.PROJECT_NAME}")
    print(f"  版本: {settings.PROJECT_VERSION}")
    print(f"  API前缀: {settings.API_V1_PREFIX}")
    print(f"  服务器地址: {settings.HOST}:{settings.PORT}")
    print(f"  调试模式: {settings.DEBUG}")
    
    print(f"\n数据库配置:")
    print(f"  MySQL: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}")
    print(f"  MongoDB: {settings.MONGODB_HOST}:{settings.MONGODB_PORT}/{settings.MONGODB_DATABASE}")
    print(f"  Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}")
    
    print(f"\nAI服务配置:")
    # LLM聚合网关配置（优先显示）
    if settings.LLM_API_KEY and settings.LLM_API_BASE:
        model_name = settings.LLM_MODEL_NAME or "未指定"
        print(f"  ✅ LLM聚合网关: 已配置")
        print(f"     - Base URL: {settings.LLM_API_BASE}")
        print(f"     - 模型名称: {model_name}")
        print(f"     - API Key: {settings.LLM_API_KEY[:10]}...{settings.LLM_API_KEY[-4:] if len(settings.LLM_API_KEY) > 14 else '***'}")
    else:
        print(f"  ⚠️  LLM聚合网关: 未配置（推荐配置）")
        if settings.LLM_API_BASE:
            print(f"     - Base URL已设置: {settings.LLM_API_BASE}")
        if settings.LLM_API_KEY:
            print(f"     - API Key已设置")
        if not settings.LLM_API_BASE and not settings.LLM_API_KEY:
            print(f"     提示: 配置 LLM_API_BASE 和 LLM_API_KEY 以使用聚合网关")
    
    # 直接调用配置（备用方案）
    print(f"\n  备用方案（直接调用）:")
    print(f"    OpenAI: {'已配置' if settings.OPENAI_API_KEY else '未配置'}")
    print(f"    Anthropic: {'已配置' if settings.ANTHROPIC_API_KEY else '未配置'}")
    print(f"    Gemini: {'已配置' if settings.GEMINI_API_KEY else '未配置'}")
    print(f"    本地LLM: {'已配置' if settings.LOCAL_LLM_URL else '未配置'}")
    
    print(f"\n文档地址:")
    print(f"  Swagger UI: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"  ReDoc: http://{settings.HOST}:{settings.PORT}/redoc")
    print(f"  健康检查: http://{settings.HOST}:{settings.PORT}/health")


def check_api_files():
    """检查API文件结构"""
    print("\n" + "=" * 80)
    print("API文件结构检查")
    print("=" * 80)
    
    api_dir = project_root / "app" / "api" / "v1"
    if not api_dir.exists():
        print(f"\n❌ API目录不存在: {api_dir}")
        return
    
    print(f"\nAPI目录: {api_dir}")
    
    api_files = list(api_dir.glob("*.py"))
    api_files = [f for f in api_files if f.name != "__init__.py"]
    
    print(f"\n发现 {len(api_files)} 个API文件:\n")
    
    for api_file in sorted(api_files):
        file_size = api_file.stat().st_size
        print(f"  ✓ {api_file.name:30} ({file_size:,} bytes)")
        
        # 检查文件是否定义了router
        try:
            with open(api_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'router = APIRouter()' in content or 'router = APIRouter(' in content:
                    print(f"    └─ 已定义 router")
                else:
                    print(f"    └─ ⚠️  未找到 router 定义")
        except Exception as e:
            print(f"    └─ ❌ 读取文件失败: {e}")


def check_main_registration():
    """检查main.py中的路由注册"""
    print("\n" + "=" * 80)
    print("路由注册检查")
    print("=" * 80)
    
    main_file = project_root / "app" / "main.py"
    if not main_file.exists():
        print(f"\n❌ main.py不存在: {main_file}")
        return
    
    try:
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找include_router调用
        import re
        router_pattern = r'app\.include_router\((\w+)\.router'
        routers = re.findall(router_pattern, content)
        
        print(f"\n在main.py中注册的路由模块 ({len(routers)} 个):\n")
        for router in routers:
            print(f"  ✓ {router}")
        
        # 检查导入
        import_pattern = r'from app\.api\.v1 import ([^#\n]+)'
        imports = re.findall(import_pattern, content)
        if imports:
            print(f"\n导入的模块:")
            imported_modules = [m.strip() for m in imports[0].split(',')]
            for module in imported_modules:
                print(f"  ✓ {module}")
        
    except Exception as e:
        print(f"\n❌ 检查失败: {e}")


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("品牌分析系统 - API配置检查工具")
    print("=" * 80)
    
    try:
        check_api_config()
        check_api_files()
        check_main_registration()
        check_api_routes()
        
        print("\n" + "=" * 80)
        print("检查完成！")
        print("=" * 80)
        print("\n提示:")
        print("  - 访问 http://localhost:8000/docs 查看完整的API文档")
        print("  - 访问 http://localhost:8000/redoc 查看ReDoc格式的API文档")
        print("  - 查看 docs/api_design.md 了解API设计规范")
        print("  - 查看 docs/新API配置指南.md 了解如何添加新API")
        
    except Exception as e:
        logger.error(f"检查失败: {e}", exc_info=True)
        print(f"\n❌ 检查失败: {e}")


if __name__ == "__main__":
    main()

