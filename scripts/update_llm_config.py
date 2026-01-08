"""
直接更新LLM聚合网关配置
"""
import sys
import io
import os
from pathlib import Path

# 设置Windows控制台编码为UTF-8
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

project_root = Path(__file__).parent.parent
env_file = project_root / ".env"
env_template = project_root / "env_template.txt"

def update_config(base_url, api_key, model_name):
    """更新配置"""
    print("\n" + "=" * 80)
    print("更新LLM聚合网关配置")
    print("=" * 80)
    
    # 修复Base URL的双斜杠
    if base_url.endswith('//v1'):
        base_url = base_url.replace('//v1', '/v1')
        print(f"\n修复Base URL: {base_url}")
    
    # 读取模板或现有文件
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    elif env_template.exists():
        with open(env_template, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    else:
        print("错误：找不到配置文件模板")
        return False
    
    # 更新配置
    new_lines = []
    llm_base_found = False
    llm_key_found = False
    llm_model_found = False
    
    for line in lines:
        if line.strip().startswith('LLM_API_BASE='):
            new_lines.append(f"LLM_API_BASE={base_url}\n")
            llm_base_found = True
        elif line.strip().startswith('LLM_API_KEY='):
            new_lines.append(f"LLM_API_KEY={api_key}\n")
            llm_key_found = True
        elif line.strip().startswith('LLM_MODEL_NAME='):
            new_lines.append(f"LLM_MODEL_NAME={model_name}\n")
            llm_model_found = True
        else:
            new_lines.append(line)
    
    # 如果配置项不存在，添加到文件末尾
    if not llm_base_found or not llm_key_found or not llm_model_found:
        # 找到AI配置部分的位置
        insert_pos = len(new_lines)
        for i, line in enumerate(new_lines):
            if '# AI配置' in line or 'LLM_API' in line:
                insert_pos = i
                break
        
        if not llm_base_found:
            new_lines.insert(insert_pos, f"LLM_API_BASE={base_url}\n")
        if not llm_key_found:
            new_lines.insert(insert_pos + 1, f"LLM_API_KEY={api_key}\n")
        if not llm_model_found:
            new_lines.insert(insert_pos + 2, f"LLM_MODEL_NAME={model_name}\n")
    
    # 写入文件
    try:
        # 备份原文件
        if env_file.exists():
            backup_file = env_file.with_suffix('.env.backup')
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"\n已备份原文件到: {backup_file}")
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print(f"\n✅ 配置已更新")
        print(f"\n配置信息：")
        print(f"  Base URL: {base_url}")
        print(f"  模型名称: {model_name}")
        print(f"  API Key: {api_key[:10]}...{api_key[-4:]}")
        
        return True
    except Exception as e:
        print(f"\n❌ 更新失败: {e}")
        return False

if __name__ == "__main__":
    # 用户提供的配置
    base_url = "https://xy.xiaoxu030.xyz:8888/v1"  # 已修复双斜杠
    api_key = "sk-gwCyORqv81gZ9Vi38pcPfNfhfv87bIzHVAqyPm5kNgufmpTn"
    model_name = "gemini-3-pro-preview-cli"
    
    try:
        if update_config(base_url, api_key, model_name):
            print("\n" + "=" * 80)
            print("配置完成！")
            print("\n下一步：")
            print("  1. 运行 'python scripts/check_llm_config.py' 验证配置")
            print("  2. 重启服务使配置生效")
            print("=" * 80)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


