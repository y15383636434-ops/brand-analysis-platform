"""
快速检查LLM聚合网关配置
"""
import sys
import os
from pathlib import Path

# 设置Windows控制台编码为UTF-8
if sys.platform == 'win32':
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings

def check_llm_config():
    """检查LLM配置"""
    print("\n" + "=" * 80)
    print("LLM聚合网关配置检查")
    print("=" * 80)
    
    if settings.LLM_API_KEY and settings.LLM_API_BASE:
        print("\n✅ LLM聚合网关已配置！")
        print(f"\n配置信息：")
        print(f"  Base URL: {settings.LLM_API_BASE}")
        
        # 检查Base URL格式
        if settings.LLM_API_BASE.endswith('//v1'):
            print(f"  ⚠️  警告：Base URL末尾有双斜杠，建议修复为: {settings.LLM_API_BASE.replace('//v1', '/v1')}")
        elif not settings.LLM_API_BASE.endswith('/v1'):
            print(f"  ⚠️  警告：Base URL应该以 /v1 结尾")
        else:
            print(f"  ✅ Base URL格式正确")
        
        model_name = settings.LLM_MODEL_NAME or "未指定"
        print(f"  模型名称: {model_name}")
        
        # 显示API Key（部分隐藏）
        if len(settings.LLM_API_KEY) > 14:
            masked_key = f"{settings.LLM_API_KEY[:10]}...{settings.LLM_API_KEY[-4:]}"
        else:
            masked_key = "***"
        print(f"  API Key: {masked_key}")
        
        print(f"\n✅ 配置状态：可以使用")
        print(f"\n提示：")
        print(f"  - 启动服务后，系统将优先使用LLM聚合网关")
        print(f"  - 如果网关失败，会自动降级到备用方案（如果已配置）")
        
    else:
        print("\n⚠️  LLM聚合网关未配置")
        print(f"\n当前状态：")
        if settings.LLM_API_BASE:
            print(f"  ✅ Base URL已设置: {settings.LLM_API_BASE}")
        else:
            print(f"  ❌ Base URL未设置")
        
        if settings.LLM_API_KEY:
            print(f"  ✅ API Key已设置")
        else:
            print(f"  ❌ API Key未设置")
        
        print(f"\n配置方法：")
        print(f"  1. 创建或编辑 .env 文件")
        print(f"  2. 添加以下配置：")
        print(f"     LLM_API_BASE=https://xy.xiaoxu030.xyz:8888/v1")
        print(f"     LLM_API_KEY=sk-您的密钥")
        print(f"     LLM_MODEL_NAME=gpt-4o-mini")
        print(f"\n  或运行配置助手：")
        print(f"     python scripts/setup_llm_config.py")
    
    # 检查备用方案
    print(f"\n备用方案（直接调用）：")
    has_backup = False
    if settings.OPENAI_API_KEY:
        print(f"  ✅ OpenAI已配置")
        has_backup = True
    else:
        print(f"  ⚠️  OpenAI未配置")
    
    if settings.GEMINI_API_KEY:
        print(f"  ✅ Gemini已配置")
        has_backup = True
    else:
        print(f"  ⚠️  Gemini未配置")
    
    if settings.ANTHROPIC_API_KEY:
        print(f"  ✅ Anthropic已配置")
        has_backup = True
    else:
        print(f"  ⚠️  Anthropic未配置")
    
    if not has_backup:
        print(f"\n💡 提示：建议配置至少一个备用方案，以防聚合网关故障")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    try:
        check_llm_config()
    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

