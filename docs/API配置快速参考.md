# API配置快速参考

> 最后更新：2026-01-07

## 📊 当前API统计

- **总API端点**: 43个
- **API模块数**: 10个
- **API版本**: v1
- **基础路径**: `/api/v1`

## 🔍 快速检查API配置

运行以下命令检查API配置：

```bash
python scripts/check_api_config.py
```

## 📁 API模块列表

| 模块 | 文件 | 端点数量 | 功能 |
|------|------|---------|------|
| 品牌管理 | `brands.py` | 5 | 品牌的CRUD操作 |
| 数据采集 | `crawl_tasks.py` | 3 | 爬虫任务管理 |
| 数据分析 | `analysis_tasks.py` | 2 | AI分析任务 |
| 报告生成 | `reports.py` | 3 | 报告生成和下载 |
| 数据查看 | `data_viewer.py` | 4 | 查看爬取的数据 |
| MediaCrawler界面 | `mediacrawler_ui.py` | 9 | MediaCrawler集成 |
| 数据分析 | `data_analysis.py` | 6 | 数据分析处理 |
| 数据展示 | `data_display.py` | 3 | 数据展示界面 |
| 爬虫界面 | `crawler_ui.py` | 2 | 爬虫UI |
| 统一控制台 | `dashboard.py` | 1 | Dashboard |

## 🛠️ 添加新API的快速步骤

### 1. 创建API文件

在 `app/api/v1/` 目录下创建新文件，例如 `my_api.py`：

```python
from fastapi import APIRouter
router = APIRouter()

@router.get("/my-endpoint")
async def my_endpoint():
    return {"message": "Hello"}
```

### 2. 注册路由

在 `app/main.py` 中：

```python
# 导入
from app.api.v1 import my_api

# 注册
app.include_router(my_api.router, prefix=settings.API_V1_PREFIX, tags=["我的API"])
```

### 3. 测试

访问 http://localhost:8000/docs 查看新API

## 📚 详细文档

- [新API配置指南](新API配置指南.md) - 完整的API开发指南
- [API设计文档](api_design.md) - API设计规范
- [项目架构文档](../项目架构文档.md) - 整体架构说明

## 🔗 重要链接

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

## ⚙️ 配置检查

### 数据库配置
- MySQL: `localhost:3306/brand_analysis`
- MongoDB: `localhost:27017/brand_analysis`
- Redis: `localhost:6379/0`

### AI服务配置状态
- OpenAI: ⚠️ 未配置
- Anthropic: ⚠️ 未配置
- Gemini: ⚠️ 未配置
- 本地LLM: ⚠️ 未配置

> 💡 提示：如需使用AI分析功能，请在 `config.py` 或环境变量中配置相应的API密钥。

## 📝 API端点分类

### 品牌管理 (5个端点)
- `POST /api/v1/brands` - 创建品牌
- `GET /api/v1/brands` - 获取品牌列表
- `GET /api/v1/brands/{brand_id}` - 获取品牌详情
- `PUT /api/v1/brands/{brand_id}` - 更新品牌
- `DELETE /api/v1/brands/{brand_id}` - 删除品牌

### 数据采集 (3个端点)
- `POST /api/v1/brands/{brand_id}/crawl` - 启动爬虫任务
- `GET /api/v1/crawl-tasks` - 获取任务列表
- `GET /api/v1/crawl-tasks/{task_id}` - 获取任务详情

### 数据分析 (8个端点)
- `POST /api/v1/brands/{brand_id}/analyze` - 启动分析任务
- `GET /api/v1/brands/{brand_id}/analysis` - 获取分析结果
- `GET /api/v1/data-analysis` - 数据分析页面
- `POST /api/v1/data-analysis/process` - 处理数据
- `GET /api/v1/data-analysis/result` - 获取分析结果
- 等等...

### MediaCrawler (9个端点)
- `POST /api/v1/mediacrawler/start` - 启动爬取
- `GET /api/v1/mediacrawler/crawl/monitor/{process_id}` - 监控页面
- `GET /api/v1/mediacrawler/crawl/output/{process_id}` - 获取输出
- 等等...

## 🚀 快速启动

```bash
# 方式1：一键启动
python 一键启动.py

# 方式2：手动启动
uvicorn app.main:app --reload
```

## 📋 检查清单

添加新API时，请确认：

- [ ] API文件已创建
- [ ] 定义了 `router = APIRouter()`
- [ ] 在 `main.py` 中导入并注册
- [ ] 添加了适当的标签（tags）
- [ ] 响应格式符合规范
- [ ] 已添加错误处理
- [ ] 已在Swagger UI中测试

---

**需要帮助？** 查看 [新API配置指南](新API配置指南.md) 获取详细说明。


