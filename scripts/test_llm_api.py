"""
测试LLM聚合网关API配置

注意：这不是pytest测试文件，请直接运行：
    python scripts/test_llm_api.py
"""
import sys
import io
import os
import asyncio
from pathlib import Path

# 防止被pytest识别为测试文件
if __name__ != "__main__":
    # 如果被pytest导入，直接退出
    import pytest
    pytest.skip("这不是pytest测试文件，请直接运行: python scripts/test_llm_api.py", allow_module_level=True)

# 设置Windows控制台编码为UTF-8
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings


async def test_llm_api():
    """测试LLM API调用"""
    print("\n" + "=" * 80)
    print("LLM聚合网关API测试")
    print("=" * 80)
    
    # 检查配置
    print("\n1. 检查配置...")
    if not settings.LLM_API_KEY or not settings.LLM_API_BASE:
        print("  ❌ LLM聚合网关未配置")
        print("\n请先配置LLM聚合网关：")
        print("  运行: python scripts/check_llm_config.py")
        return False
    
    print(f"  ✅ Base URL: {settings.LLM_API_BASE}")
    print(f"  ✅ 模型名称: {settings.LLM_MODEL_NAME or '未指定'}")
    print(f"  ✅ API Key: {settings.LLM_API_KEY[:10]}...{settings.LLM_API_KEY[-4:]}")
    
    # 测试API调用
    print("\n2. 测试API调用...")
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_API_BASE
        )
        
        model_name = settings.LLM_MODEL_NAME or "gpt-4o-mini"
        test_prompt = "请用一句话介绍你自己。"
        
        print(f"  发送测试请求...")
        print(f"  模型: {model_name}")
        print(f"  提示: {test_prompt}")
        
        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": test_prompt}
            ],
            max_tokens=100,
            timeout=30.0
        )
        
        result = response.choices[0].message.content
        print(f"\n  ✅ API调用成功！")
        print(f"\n  响应内容:")
        print(f"  {result}")
        
        return True
        
    except Exception as e:
        print(f"\n  ❌ API调用失败")
        print(f"  错误信息: {str(e)}")
        print(f"\n  可能的原因：")
        print(f"  1. Base URL不正确（应该以 /v1 结尾）")
        print(f"  2. API Key无效或已过期")
        print(f"  3. 模型名称不存在")
        print(f"  4. 网络连接问题")
        print(f"  5. 聚合网关服务不可用")
        return False


async def test_ai_service():
    """测试AI服务集成"""
    print("\n" + "=" * 80)
    print("AI服务集成测试")
    print("=" * 80)
    
    try:
        from app.services.ai_service import ai_service
        
        print("\n1. 测试情感分析...")
        test_text = "这个产品非常好用，我很满意！"
        result = ai_service.analyze_sentiment(test_text)
        print(f"  测试文本: {test_text}")
        print(f"  情感: {result.get('sentiment')}")
        print(f"  分数: {result.get('score')}")
        print("  ✅ 情感分析正常")
        
        print("\n2. 测试关键词提取...")
        keywords = ai_service.extract_keywords(test_text, top_k=5)
        print(f"  提取的关键词: {[kw.get('keyword') for kw in keywords]}")
        print("  ✅ 关键词提取正常")
        
        print("\n3. 测试LLM深度分析...")
        print("  调用LLM进行深度分析...")
        try:
            llm_result = await ai_service.analyze_with_llm(
                brand_name="测试品牌",
                data_summary={
                    "total_count": 10,
                    "sentiment_distribution": {"positive": 70, "negative": 10, "neutral": 20},
                    "avg_sentiment_score": 0.75,
                    "keywords": [{"keyword": "测试"}]
                },
                analysis_type="comprehensive"
            )
            print(f"  使用的模型: {llm_result.get('model')}")
            insights = llm_result.get('insights', '')
            if isinstance(insights, dict):
                import json
                print(f"  分析结果: {json.dumps(insights, ensure_ascii=False)[:100]}...")
            else:
                print(f"  分析结果: {str(insights)[:100]}...")
            print("  ✅ LLM分析正常")
            return True
        except Exception as e:
            print(f"  ⚠️  LLM分析失败: {str(e)}")
            print("  提示：这可能是正常的，如果LLM API未配置或调用失败")
            return False
            
    except Exception as e:
        print(f"\n  ❌ AI服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("品牌分析系统 - API配置测试")
    print("=" * 80)
    
    # 运行测试
    loop = asyncio.get_event_loop()
    
    # 测试1: LLM API
    print("\n" + "=" * 80)
    api_ok = loop.run_until_complete(test_llm_api())
    
    # 测试2: AI服务集成
    service_ok = loop.run_until_complete(test_ai_service())
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"\nLLM API测试: {'✅ 通过' if api_ok else '❌ 失败'}")
    print(f"AI服务测试: {'✅ 通过' if service_ok else '⚠️  部分失败'}")
    
    if api_ok:
        print("\n✅ 配置正确，API可以正常使用！")
        print("\n下一步：")
        print("  1. 启动服务: python app/main.py")
        print("  2. 访问 Swagger UI: http://localhost:8000/docs")
        print("  3. 测试品牌分析API")
    else:
        print("\n⚠️  请检查配置后重试")
        print("\n检查配置：")
        print("  python scripts/check_llm_config.py")
    
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

