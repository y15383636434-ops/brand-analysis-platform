"""
检查AI配置脚本
用于检查AI分析功能的配置是否正确
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 设置控制台编码为UTF-8（Windows）
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def check_ai_config():
    """检查AI配置"""
    print("=" * 60)
    print("AI分析配置检查")
    print("=" * 60)
    
    # 加载.env文件
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv()
        print("[OK] 找到 .env 文件")
    else:
        print("[X] 未找到 .env 文件")
        print("[提示] 请创建 .env 文件并配置AI API密钥")
        print("   参考 env_template.txt 或 AI分析接入指南.md")
        return False
    
    print("\n📋 当前配置状态：")
    print("-" * 60)
    
    # 检查OpenAI配置
    openai_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4")
    
    if openai_key:
        masked_key = openai_key[:10] + "..." if len(openai_key) > 10 else "***"
        print(f"[OK] OpenAI配置已设置")
        print(f"   API Key: {masked_key}")
        print(f"   Base URL: {openai_base_url or '默认 (api.openai.com)'}")
        print(f"   Model: {openai_model}")
        print("   [使用] 将使用 OpenAI 进行AI分析")
        return True
    else:
        print("[X] OpenAI配置未设置")
    
    # 检查Gemini配置
    gemini_key = os.getenv("GEMINI_API_KEY")
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
    
    if gemini_key:
        masked_key = gemini_key[:10] + "..." if len(gemini_key) > 10 else "***"
        print(f"[OK] Gemini配置已设置")
        print(f"   API Key: {masked_key}")
        print(f"   Model: {gemini_model}")
        print("   [使用] 将使用 Gemini 进行AI分析")
        return True
    else:
        print("[X] Gemini配置未设置")
    
    # 检查Claude配置
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    
    if anthropic_key:
        masked_key = anthropic_key[:10] + "..." if len(anthropic_key) > 10 else "***"
        print(f"[OK] Claude配置已设置")
        print(f"   API Key: {masked_key}")
        print(f"   Model: {anthropic_model}")
        print("   [使用] 将使用 Claude 进行AI分析")
        return True
    else:
        print("[X] Claude配置未设置")
    
    # 检查本地LLM配置
    local_llm_url = os.getenv("LOCAL_LLM_URL")
    local_llm_model = os.getenv("LOCAL_LLM_MODEL")
    
    if local_llm_url:
        print(f"[OK] 本地LLM配置已设置")
        print(f"   URL: {local_llm_url}")
        print(f"   Model: {local_llm_model or '未指定'}")
        print("   [使用] 将使用本地LLM进行AI分析")
        return True
    else:
        print("[X] 本地LLM配置未设置")
    
    print("\n" + "=" * 60)
    print("[警告] 未配置任何AI API")
    print("=" * 60)
    print("\n[提示] 配置建议：")
    print("   1. 在 .env 文件中配置以下之一：")
    print("      - GEMINI_API_KEY=your-key (推荐)")
    print("      - OPENAI_API_KEY=your-key")
    print("      - ANTHROPIC_API_KEY=your-key")
    print("      - LOCAL_LLM_URL=http://localhost:11434/v1/chat/completions")
    print("\n   2. 如果不配置LLM API：")
    print("      [OK] 基础分析（情感、关键词）仍可使用")
    print("      [X] AI深度洞察功能不可用")
    print("\n   详细说明请查看：AI分析接入指南.md")
    
    return False

def check_dependencies():
    """检查依赖包"""
    print("\n" + "=" * 60)
    print("📦 检查依赖包")
    print("=" * 60)
    
    dependencies = {
        "openai": "OpenAI API客户端",
        "google.generativeai": "Gemini API客户端",
        "anthropic": "Claude API客户端",
        "httpx": "HTTP客户端（本地LLM需要）",
        "jieba": "中文分词",
        "snownlp": "中文情感分析"
    }
    
    missing = []
    for package, desc in dependencies.items():
        try:
            __import__(package)
            print(f"[OK] {package:15} - {desc}")
        except ImportError:
            print(f"[X] {package:15} - {desc} (未安装)")
            missing.append(package)
    
    if missing:
        print(f"\n[警告] 缺少依赖包: {', '.join(missing)}")
        print("[提示] 安装命令: pip install " + " ".join(missing))
        return False
    
    return True

def main():
    """主函数"""
    print("\n")
    ai_configured = check_ai_config()
    deps_ok = check_dependencies()
    
    print("\n" + "=" * 60)
    print("📊 检查结果总结")
    print("=" * 60)
    
    if ai_configured and deps_ok:
        print("[OK] 配置完整，可以开始使用AI分析功能！")
        print("\n[下一步]")
        print("   1. 确保服务已启动（FastAPI + Celery）")
        print("   2. 访问 http://localhost:8000/docs 查看API文档")
        print("   3. 使用 POST /api/v1/brands/{brand_id}/analyze 启动分析")
    elif deps_ok:
        print("[警告] AI API未配置，但基础分析功能可用")
        print("[提示] 配置AI API后可启用深度洞察功能")
    else:
        print("[X] 需要安装依赖包")
    
    print("\n")

if __name__ == "__main__":
    main()

