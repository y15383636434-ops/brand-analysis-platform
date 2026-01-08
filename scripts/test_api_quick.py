"""
快速测试API配置（简单版本）
"""
import sys
import io
import os
import asyncio
from pathlib import Path

# 设置Windows控制台编码为UTF-8
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings


async def quick_test():
    """快速测试"""
    print("\n" + "=" * 80)
    print("快速API测试")
    print("=" * 80)
    
    # 检查配置
    if not settings.LLM_API_KEY or not settings.LLM_API_BASE:
        print("\n❌ LLM聚合网关未配置")
        print("\n请先配置：")
        print("  1. 检查配置: python scripts/check_llm_config.py")
        print("  2. 更新配置: python scripts/update_llm_config.py")
        return False
    
    print(f"\n配置信息：")
    print(f"  Base URL: {settings.LLM_API_BASE}")
    print(f"  模型: {settings.LLM_MODEL_NAME or '未指定'}")
    
    # 测试调用
    print(f"\n正在测试API调用...")
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_API_BASE,
            timeout=30.0
        )
        
        model = settings.LLM_MODEL_NAME or "gpt-4o-mini"
        
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "你好"}],
            max_tokens=50
        )
        
        result = response.choices[0].message.content
        print(f"\n✅ API测试成功！")
        print(f"\n响应: {result}")
        print(f"\n✅ 配置正确，可以正常使用！")
        return True
        
    except Exception as e:
        print(f"\n❌ API测试失败")
        print(f"错误: {str(e)}")
        print(f"\n请检查：")
        print(f"  1. Base URL是否正确（应以 /v1 结尾）")
        print(f"  2. API Key是否有效")
        print(f"  3. 模型名称是否正确")
        print(f"  4. 网络连接是否正常")
        return False


if __name__ == "__main__":
    try:
        result = asyncio.run(quick_test())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n测试已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


