"""
获取聚合网关中可用的模型列表
"""
import sys
import io
import os
import asyncio
import httpx
from pathlib import Path

if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings


async def get_models_from_api():
    """尝试从API获取模型列表"""
    print("\n尝试从API获取模型列表...")
    
    base_url = settings.LLM_API_BASE
    api_key = settings.LLM_API_KEY
    
    if not base_url or not api_key:
        print("  ❌ 配置不完整")
        return []
    
    try:
        # 尝试调用models端点
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            # 尝试不同的端点
            endpoints = [
                f"{base_url.rstrip('/v1')}/v1/models",
                f"{base_url}/models",
                f"{base_url.rstrip('/v1')}/api/v1/models",
            ]
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            for endpoint in endpoints:
                try:
                    print(f"  尝试: {endpoint}")
                    response = await client.get(endpoint, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        if 'data' in data:
                            models = [m.get('id') for m in data['data']]
                            print(f"  ✅ 成功获取模型列表")
                            return models
                except:
                    continue
            
            print("  ⚠️  无法从API获取模型列表")
            return []
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return []


async def test_common_models():
    """测试常见模型名称"""
    print("\n测试常见模型名称...")
    
    # 根据错误信息，尝试更多可能的模型名称
    models_to_test = [
        # Gemini模型
        "gemini-3-pro-preview-cli",
        "gemini-3-pro-preview",
        "gemini-3-pro",
        "gemini-pro",
        "gemini-2.0-flash-exp",
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        
        # GPT模型
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
        
        # Claude模型
        "claude-3-5-sonnet",
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku",
        
        # 其他可能的命名
        "gemini-pro-cli",
        "gemini-pro-preview",
    ]
    
    working_models = []
    
    from openai import AsyncOpenAI
    client = AsyncOpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_API_BASE,
        timeout=15.0
    )
    
    for model in models_to_test:
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=10
            )
            result = response.choices[0].message.content
            print(f"  ✅ {model} - 可用")
            working_models.append(model)
        except Exception as e:
            error_msg = str(e)
            if "model_not_found" in error_msg or "无可用渠道" in error_msg:
                # 模型不存在，跳过
                pass
            elif "522" in error_msg or "523" in error_msg:
                # 超时，但模型可能存在
                print(f"  ⚠️  {model} - 超时（可能可用但响应慢）")
            else:
                # 其他错误
                pass
    
    return working_models


async def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("查找可用模型")
    print("=" * 80)
    
    if not settings.LLM_API_KEY or not settings.LLM_API_BASE:
        print("\n❌ 配置不完整")
        print("请先配置LLM聚合网关")
        return
    
    print(f"\nBase URL: {settings.LLM_API_BASE}")
    print(f"API Key: {settings.LLM_API_KEY[:10]}...{settings.LLM_API_KEY[-4:]}")
    
    # 方法1：从API获取
    api_models = await get_models_from_api()
    
    # 方法2：测试常见模型
    working_models = await test_common_models()
    
    # 合并结果
    all_models = list(set(api_models + working_models))
    
    print("\n" + "=" * 80)
    print("结果总结")
    print("=" * 80)
    
    if all_models:
        print(f"\n✅ 找到 {len(all_models)} 个可用模型：")
        for model in all_models:
            print(f"  - {model}")
        
        recommended = all_models[0]
        print(f"\n推荐使用: {recommended}")
        print(f"\n更新配置：")
        print(f"  编辑 .env 文件，设置：")
        print(f"  LLM_MODEL_NAME={recommended}")
        print(f"\n或运行：")
        print(f"  python scripts/update_llm_config.py")
    else:
        print(f"\n⚠️  未找到可用模型")
        print(f"\n建议：")
        print(f"  1. 登录聚合网关管理台：{settings.LLM_API_BASE.rstrip('/v1')}/console")
        print(f"  2. 查看'渠道'或'模型'页面，确认已配置的模型")
        print(f"  3. 检查模型名称是否正确")
        print(f"  4. 确认模型渠道是否启用")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试已取消")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


