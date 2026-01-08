"""
真正的pytest测试文件
如果需要在PyCharm中使用pytest运行器，可以使用这个文件
"""
import pytest
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

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings


@pytest.fixture
def ai_service():
    """AI服务fixture"""
    from app.services.ai_service import ai_service
    return ai_service


@pytest.mark.asyncio
async def test_llm_api_configuration():
    """测试LLM API配置"""
    assert settings.LLM_API_KEY is not None, "LLM_API_KEY未配置"
    assert settings.LLM_API_BASE is not None, "LLM_API_BASE未配置"
    assert settings.LLM_MODEL_NAME is not None, "LLM_MODEL_NAME未配置"


@pytest.mark.asyncio
async def test_llm_api_call():
    """测试LLM API调用"""
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
    
    assert response.choices[0].message.content is not None
    print(f"\n✅ LLM API调用成功")
    print(f"响应: {response.choices[0].message.content[:100]}")


def test_sentiment_analysis(ai_service):
    """测试情感分析"""
    test_text = "这个产品非常好用，我很满意！"
    result = ai_service.analyze_sentiment(test_text)
    
    assert result['sentiment'] in ['positive', 'negative', 'neutral']
    assert 0 <= result['score'] <= 1
    print(f"\n✅ 情感分析: {result['sentiment']}, 分数: {result['score']}")


def test_keyword_extraction(ai_service):
    """测试关键词提取"""
    test_text = "这个产品非常好用，我很满意！"
    keywords = ai_service.extract_keywords(test_text, top_k=5)
    
    assert len(keywords) > 0
    assert isinstance(keywords, list)
    print(f"\n✅ 提取的关键词: {[kw.get('keyword') for kw in keywords]}")


@pytest.mark.asyncio
async def test_llm_analysis(ai_service):
    """测试LLM深度分析"""
    data_summary = {
        "total_count": 10,
        "sentiment_distribution": {"positive": 70, "negative": 10, "neutral": 20},
        "avg_sentiment_score": 0.75,
        "keywords": [{"keyword": "测试"}]
    }
    
    result = await ai_service.analyze_with_llm(
        brand_name="测试品牌",
        data_summary=data_summary,
        analysis_type="comprehensive"
    )
    
    assert result['model'] is not None
    assert result['insights'] is not None
    print(f"\n✅ LLM分析成功")
    print(f"使用的模型: {result['model']}")
    print(f"分析结果: {result['insights'][:100]}...")


if __name__ == "__main__":
    # 如果直接运行，使用pytest
    pytest.main([__file__, "-v", "-s"])


