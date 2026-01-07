"""
清理Python缓存文件
"""
import os
import shutil
import sys
from pathlib import Path

def clean_pycache(root_dir):
    """清理所有__pycache__目录和.pyc文件"""
    root = Path(root_dir)
    removed_dirs = []
    removed_files = []
    
    # 查找所有__pycache__目录
    for pycache_dir in root.rglob('__pycache__'):
        if pycache_dir.is_dir():
            try:
                shutil.rmtree(pycache_dir)
                removed_dirs.append(str(pycache_dir.relative_to(root)))
                print(f"已删除目录: {pycache_dir.relative_to(root)}")
            except Exception as e:
                print(f"删除失败 {pycache_dir}: {e}")
    
    # 查找所有.pyc文件
    for pyc_file in root.rglob('*.pyc'):
        if pyc_file.is_file():
            try:
                pyc_file.unlink()
                removed_files.append(str(pyc_file.relative_to(root)))
                print(f"已删除文件: {pyc_file.relative_to(root)}")
            except Exception as e:
                print(f"删除失败 {pyc_file}: {e}")
    
    print("\n" + "=" * 60)
    print(f"清理完成！")
    print(f"删除了 {len(removed_dirs)} 个__pycache__目录")
    print(f"删除了 {len(removed_files)} 个.pyc文件")
    print("=" * 60)

if __name__ == "__main__":
    # 排除MediaCrawler的python_env目录（虚拟环境，不需要清理）
    project_root = Path(__file__).parent
    
    print("=" * 60)
    print("清理Python缓存文件")
    print("=" * 60)
    print(f"项目根目录: {project_root}")
    print("\n开始清理...\n")
    
    clean_pycache(project_root)



