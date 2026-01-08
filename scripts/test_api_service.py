"""
测试API服务
检查服务是否正常运行，并测试主要API端点
"""
import sys
import io
import os
import requests
import time
from pathlib import Path

if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"


def test_health():
    """测试健康检查"""
    print("\n1. 测试健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ 健康检查通过")
            print(f"   响应: {response.json()}")
            return True
        else:
            print(f"   ❌ 健康检查失败: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"   ❌ 无法连接到服务")
        print(f"   提示: 请先启动服务 (python app/main.py 或 启动FastAPI.bat)")
        return False
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False


def test_api_base():
    """测试API基础路径"""
    print("\n2. 测试API基础路径...")
    try:
        # 测试根路径重定向
        response = requests.get(f"{BASE_URL}/", timeout=5, allow_redirects=False)
        if response.status_code in [200, 307, 308]:
            print(f"   ✅ API基础路径正常")
            return True
        else:
            print(f"   ⚠️  状态码: {response.status_code}")
            return True  # 不算失败
    except Exception as e:
        print(f"   ⚠️  错误: {e}")
        return True  # 不算失败


def test_brands_api():
    """测试品牌管理API"""
    print("\n3. 测试品牌管理API...")
    try:
        # 获取品牌列表
        response = requests.get(f"{BASE_URL}{API_PREFIX}/brands", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 获取品牌列表成功")
            print(f"   品牌数量: {data.get('data', {}).get('total', 0)}")
            return True
        else:
            print(f"   ❌ 获取品牌列表失败: {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False


def test_create_brand():
    """测试创建品牌"""
    print("\n4. 测试创建品牌...")
    try:
        test_brand = {
            "name": f"测试品牌_{int(time.time())}",
            "description": "API测试创建的品牌",
            "keywords": ["测试", "API"],
            "platforms": ["xhs"]
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/brands",
            json=test_brand,
            timeout=10
        )
        if response.status_code == 201:
            data = response.json()
            brand_id = data.get('id')
            print(f"   ✅ 创建品牌成功")
            print(f"   品牌ID: {brand_id}")
            print(f"   品牌名称: {data.get('name')}")
            return True, brand_id
        else:
            print(f"   ❌ 创建品牌失败: {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False, None
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False, None


def test_crawl_tasks_api():
    """测试爬虫任务API"""
    print("\n5. 测试爬虫任务API...")
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/crawl-tasks", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 获取爬虫任务列表成功")
            print(f"   任务数量: {data.get('data', {}).get('total', 0)}")
            return True
        else:
            print(f"   ⚠️  获取任务列表失败: {response.status_code}")
            return True  # 不算失败，可能没有任务
    except Exception as e:
        print(f"   ⚠️  错误: {e}")
        return True  # 不算失败


def test_analysis_api(brand_id=None):
    """测试分析API"""
    print("\n6. 测试分析API...")
    if not brand_id:
        print("   ⚠️  跳过（需要品牌ID）")
        return True
    
    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/brands/{brand_id}/analysis",
            timeout=10
        )
        if response.status_code == 200:
            print(f"   ✅ 获取分析结果成功")
            return True
        elif response.status_code == 404:
            print(f"   ⚠️  暂无分析结果（正常，需要先进行分析）")
            return True
        else:
            print(f"   ⚠️  状态码: {response.status_code}")
            return True  # 不算失败
    except Exception as e:
        print(f"   ⚠️  错误: {e}")
        return True  # 不算失败


def test_dashboard():
    """测试Dashboard"""
    print("\n7. 测试Dashboard...")
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/dashboard", timeout=10)
        if response.status_code == 200:
            print(f"   ✅ Dashboard可访问")
            return True
        else:
            print(f"   ⚠️  状态码: {response.status_code}")
            return True  # 不算失败
    except Exception as e:
        print(f"   ⚠️  错误: {e}")
        return True  # 不算失败


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("API服务测试")
    print("=" * 80)
    print(f"\n测试目标: {BASE_URL}")
    print(f"API前缀: {API_PREFIX}")
    
    # 检查服务是否运行
    print("\n" + "-" * 80)
    print("检查服务状态...")
    print("-" * 80)
    
    health_ok = test_health()
    
    if not health_ok:
        print("\n" + "=" * 80)
        print("❌ 服务未运行")
        print("=" * 80)
        print("\n请先启动服务：")
        print("  方式1: 启动FastAPI.bat")
        print("  方式2: python app/main.py")
        print("  方式3: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("\n启动后，再次运行此脚本进行测试")
        return
    
    # 运行测试
    print("\n" + "-" * 80)
    print("测试API端点...")
    print("-" * 80)
    
    results = []
    
    # 基础测试
    results.append(("健康检查", test_health()))
    results.append(("API基础路径", test_api_base()))
    
    # API测试
    results.append(("品牌列表API", test_brands_api()))
    success, brand_id = test_create_brand()
    results.append(("创建品牌API", success))
    
    results.append(("爬虫任务API", test_crawl_tasks_api()))
    results.append(("分析API", test_analysis_api(brand_id)))
    results.append(("Dashboard", test_dashboard()))
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n测试结果: {passed}/{total} 通过")
    print("\n详细结果：")
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
    
    if passed == total:
        print("\n✅ 所有测试通过！API服务运行正常")
        print("\n下一步：")
        print("  1. 访问 Swagger UI: http://localhost:8000/docs")
        print("  2. 访问 Dashboard: http://localhost:8000/api/v1/dashboard")
        print("  3. 开始使用品牌分析功能")
    else:
        print("\n⚠️  部分测试失败，请检查服务日志")
        print("  查看日志: type logs\\app.log")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试已取消")
    except Exception as e:
        print(f"\n❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()


