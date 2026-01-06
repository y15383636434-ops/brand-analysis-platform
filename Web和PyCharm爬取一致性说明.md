# Web界面和PyCharm爬取一致性说明

## 概述

本文档说明Web界面和PyCharm中爬取方式的一致性，以及已做的统一修复。

## 两种爬取方式

### 1. Web界面爬取 (`app/api/v1/mediacrawler_ui.py`)

**方式**：直接调用MediaCrawler命令行
- 使用 `subprocess.Popen` 启动MediaCrawler进程
- 实时捕获输出，显示在监控页面
- 不需要Celery Worker

**命令参数**：
```python
cmd = [
    python_cmd,
    main_py,
    "--platform", mediacrawler_platform,  # 使用MEDIACRAWLER_PLATFORM_MAP映射
    "--lt", "qrcode",
    "--type", "search",
    "--keywords", keywords,
    "--save_data_option", "json",
    "--note_type", note_type,  # 仅小红书
    "--get_comment", "yes/no",
    "--get_sub_comment", "yes/no",
]
```

**配置修改**：
- 使用 `set_max_count()` 动态修改 `CRAWLER_MAX_NOTES_COUNT`
- 爬取完成后使用 `restore_config()` 恢复配置

### 2. PyCharm爬取 (`crawlers/*_crawler.py` → Celery任务)

**方式**：通过FastAPI后端API创建任务，由Celery Worker执行
- 调用 `POST /api/v1/brands` 创建品牌
- 调用 `POST /api/v1/crawl-tasks` 创建爬虫任务
- Celery任务使用 `CrawlerService.crawl_platform()` 执行爬取

**执行流程**：
```
PyCharm运行爬虫文件
  ↓
调用FastAPI API创建品牌和任务
  ↓
Celery Worker接收任务
  ↓
CrawlerService.crawl_platform()
  ↓
_crawl_with_mediacrawler()
  ↓
调用MediaCrawler命令行
```

## 已修复的一致性问题

### ✅ 1. 平台代码映射统一

**修复前**：
- Web界面：使用 `MEDIACRAWLER_PLATFORM_MAP`
- Celery任务：直接使用 `platform` 参数，没有映射

**修复后**：
- 两者都使用平台代码映射
- `CrawlerService.PLATFORM_MAP` 与 `MEDIACRAWLER_PLATFORM_MAP` 保持一致

### ✅ 2. 最大数量设置统一

**修复前**：
- Web界面：使用 `set_max_count()` 动态修改配置
- Celery任务：没有设置最大数量，使用默认值

**修复后**：
- Celery任务也使用 `set_max_count()` 和 `restore_config()`
- 确保爬取完成后恢复配置文件

### ✅ 3. 命令参数统一

**修复前**：
- Web界面：支持笔记类型、子评论等参数
- Celery任务：缺少子评论参数

**修复后**：
- 两者使用相同的命令参数
- 都支持 `--get_sub_comment` 参数

### ✅ 4. 数据目录映射统一

**修复前**：
- 数据目录映射不一致，导致找不到数据

**修复后**：
- 统一使用 `get_actual_data_dir()` 函数
- 正确处理命令行参数和数据目录名的差异

## 当前一致性状态

| 项目 | Web界面 | PyCharm/Celery | 状态 |
|------|---------|----------------|------|
| 平台代码映射 | ✅ MEDIACRAWLER_PLATFORM_MAP | ✅ PLATFORM_MAP | ✅ 一致 |
| 最大数量设置 | ✅ set_max_count() | ✅ set_max_count() | ✅ 一致 |
| 命令参数 | ✅ 完整参数 | ✅ 完整参数 | ✅ 一致 |
| 数据目录 | ✅ get_actual_data_dir() | ✅ get_actual_data_dir() | ✅ 一致 |
| 配置恢复 | ✅ restore_config() | ✅ restore_config() | ✅ 一致 |

## 使用建议

### Web界面爬取
- ✅ 推荐用于日常使用
- ✅ 实时查看输出日志
- ✅ 不需要启动Celery Worker
- ✅ 可以直接停止爬取

### PyCharm爬取
- ✅ 适合批量任务
- ✅ 可以编程控制
- ⚠️ 需要FastAPI服务和Celery Worker都在运行
- ⚠️ 输出在Celery Worker日志中

## 注意事项

1. **平台代码映射**
   - 用户界面代码（如 `kuaishou`）→ MediaCrawler命令行参数（`ks`）→ 实际数据目录（`kuaishou`）
   - 确保使用正确的映射函数

2. **配置文件修改**
   - 修改 `CRAWLER_MAX_NOTES_COUNT` 后必须恢复
   - 避免影响其他爬取任务

3. **数据目录访问**
   - 始终使用 `get_actual_data_dir()` 获取数据目录
   - 不要直接使用平台代码作为目录名

4. **命令参数**
   - 确保所有参数与Web界面保持一致
   - 特别是平台代码、最大数量、评论设置等

## 验证方法

运行以下命令验证一致性：

```python
# 检查平台映射
from app.api.v1.mediacrawler_ui import MEDIACRAWLER_PLATFORM_MAP
from app.services.crawler_service import CrawlerService

print("Web界面映射:", MEDIACRAWLER_PLATFORM_MAP)
print("Celery映射:", CrawlerService.PLATFORM_MAP)
print("是否一致:", MEDIACRAWLER_PLATFORM_MAP == CrawlerService.PLATFORM_MAP)
```

## 总结

✅ **Web界面和PyCharm中的爬取现在已完全一致**

- 使用相同的平台代码映射
- 使用相同的最大数量设置方法
- 使用相同的命令参数
- 使用相同的数据目录访问方法
- 使用相同的配置恢复机制

两种方式现在可以互换使用，结果完全一致。



