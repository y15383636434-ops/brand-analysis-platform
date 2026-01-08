"""
LLM聚合网关配置助手
帮助用户快速配置LLM聚合网关
"""
import os
import sys
import io
from pathlib import Path

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


def create_env_file():
    """创建或更新.env文件"""
    env_file = project_root / ".env"
    env_example = project_root / "env_template.txt"
    
    print("\n" + "=" * 80)
    print("LLM聚合网关配置助手")
    print("=" * 80)
    
    # 检查是否已存在.env文件
    if env_file.exists():
        print(f"\n⚠️  发现已存在的 .env 文件: {env_file}")
        response = input("是否要更新配置？(y/n): ").strip().lower()
        if response != 'y':
            print("已取消配置。")
            return
    else:
        print(f"\n📝 将创建新的 .env 文件: {env_file}")
    
    # 读取模板文件
    if env_example.exists():
        with open(env_example, 'r', encoding='utf-8') as f:
            template_content = f.read()
    else:
        template_content = ""
    
    # 获取用户输入
    print("\n" + "-" * 80)
    print("请填写以下配置信息：")
    print("-" * 80)
    
    # Base URL
    print("\n1. LLM聚合网关地址（Base URL）")
    print("   示例: https://xy.xiaoxu030.xyz:8888/v1")
    print("   ⚠️  注意：必须以 /v1 结尾，不要使用 /console")
    base_url = input("   请输入Base URL: ").strip()
    if not base_url.endswith('/v1'):
        print("   ⚠️  警告：Base URL应该以 /v1 结尾")
        confirm = input("   是否继续？(y/n): ").strip().lower()
        if confirm != 'y':
            print("已取消配置。")
            return
    
    # API Key
    print("\n2. API密钥（在聚合网关管理台生成）")
    print("   格式通常为: sk-xxxxxxxxxxxxxxxxxxxxxxx")
    api_key = input("   请输入API Key: ").strip()
    if not api_key.startswith('sk-'):
        print("   ⚠️  警告：API Key通常以 sk- 开头")
        confirm = input("   是否继续？(y/n): ").strip().lower()
        if confirm != 'y':
            print("已取消配置。")
            return
    
    # Model Name
    print("\n3. 模型名称")
    print("   常见模型: gpt-4o-mini, gpt-4o, claude-3-5-sonnet, gemini-2.0-flash-exp")
    model_name = input("   请输入模型名称（默认: gpt-4o-mini）: ").strip()
    if not model_name:
        model_name = "gpt-4o-mini"
    
    # 更新配置
    print("\n" + "-" * 80)
    print("配置摘要：")
    print(f"  Base URL: {base_url}")
    print(f"  API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else '***'}")
    print(f"  模型名称: {model_name}")
    print("-" * 80)
    
    confirm = input("\n确认保存配置？(y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消配置。")
        return
    
    # 读取现有.env内容（如果存在）
    existing_content = ""
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            existing_content = f.read()
    
    # 更新或添加LLM配置
    lines = existing_content.split('\n') if existing_content else []
    new_lines = []
    
    # 标记是否已找到LLM配置段
    llm_section_found = False
    llm_base_found = False
    llm_key_found = False
    llm_model_found = False
    
    for line in lines:
        # 检查是否是LLM配置行
        if line.strip().startswith('LLM_API_BASE='):
            new_lines.append(f"LLM_API_BASE={base_url}")
            llm_base_found = True
            llm_section_found = True
        elif line.strip().startswith('LLM_API_KEY='):
            new_lines.append(f"LLM_API_KEY={api_key}")
            llm_key_found = True
            llm_section_found = True
        elif line.strip().startswith('LLM_MODEL_NAME='):
            new_lines.append(f"LLM_MODEL_NAME={model_name}")
            llm_model_found = True
            llm_section_found = True
        else:
            new_lines.append(line)
    
    # 如果没有找到LLM配置段，添加到文件末尾
    if not llm_section_found:
        new_lines.append("")
        new_lines.append("# LLM聚合网关配置")
        new_lines.append(f"LLM_API_BASE={base_url}")
        new_lines.append(f"LLM_API_KEY={api_key}")
        new_lines.append(f"LLM_MODEL_NAME={model_name}")
    else:
        # 如果部分配置缺失，补充
        if not llm_base_found:
            # 找到LLM_API_KEY的位置，在其前面插入
            for i, line in enumerate(new_lines):
                if line.strip().startswith('LLM_API_KEY='):
                    new_lines.insert(i, f"LLM_API_BASE={base_url}")
                    break
        if not llm_key_found:
            for i, line in enumerate(new_lines):
                if line.strip().startswith('LLM_MODEL_NAME='):
                    new_lines.insert(i, f"LLM_API_KEY={api_key}")
                    break
        if not llm_model_found:
            for i, line in enumerate(new_lines):
                if line.strip().startswith('LLM_API_KEY='):
                    new_lines.insert(i + 1, f"LLM_MODEL_NAME={model_name}")
                    break
    
    # 写入文件
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        print(f"\n✅ 配置已保存到: {env_file}")
        print("\n下一步：")
        print("  1. 运行 'python scripts/check_api_config.py' 验证配置")
        print("  2. 重启FastAPI服务使配置生效")
    except Exception as e:
        print(f"\n❌ 保存配置失败: {e}")
        return


def main():
    """主函数"""
    try:
        create_env_file()
    except KeyboardInterrupt:
        print("\n\n已取消配置。")
    except Exception as e:
        print(f"\n❌ 配置过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

