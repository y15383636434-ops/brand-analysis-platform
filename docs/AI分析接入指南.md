# 🤖 AI分析接入指南

## 📋 概述

本系统已集成AI分析功能，支持：
- ✅ **情感分析** - 自动分析文本情感倾向（正面/负面/中性）
- ✅ **关键词提取** - 提取高频关键词和权重
- ✅ **文本统计** - 统计文本数量、长度、词频等
- ✅ **AI深度分析** - 使用大语言模型进行品牌深度洞察

---

## 🚀 快速开始

### 步骤1: 配置AI API密钥

AI分析功能需要配置LLM API密钥。系统支持四种方式（**选择其中一种即可**）：

#### 方式1: 使用Google Gemini（推荐）⭐

1. 获取Gemini API密钥：访问 https://aistudio.google.com/app/apikey
2. 在项目根目录创建或编辑 `.env` 文件
3. 添加以下配置：

```env
# Google Gemini配置
GEMINI_API_KEY=sk-your-gemini-api-key-here
GEMINI_MODEL=gemini-2.0-flash-exp
```

**注意**：
- Gemini API密钥格式通常以 `sk-` 开头
- 支持的模型：`gemini-2.0-flash-exp`、`gemini-1.5-pro`、`gemini-1.5-flash` 等
- Gemini API通常有免费额度，适合测试使用

#### 方式2: 使用OpenAI

1. 获取OpenAI API密钥：访问 https://platform.openai.com/api-keys
2. 在项目根目录创建或编辑 `.env` 文件
3. 添加以下配置：

```env
# OpenAI配置
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
```

**注意**：
- 如果使用OpenAI官方API，`OPENAI_BASE_URL` 可以省略
- 如果使用代理服务（如OpenRouter、OneAPI等），需要设置 `OPENAI_BASE_URL`
- 模型名称可以是：`gpt-4`、`gpt-3.5-turbo`、`gpt-4-turbo` 等

#### 方式3: 使用Claude（Anthropic）

1. 获取Anthropic API密钥：访问 https://console.anthropic.com/
2. 在 `.env` 文件中添加：

```env
# Anthropic (Claude)配置
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

#### 方式4: 使用本地LLM（如Ollama、本地部署的模型）

1. 确保本地LLM服务已启动（如Ollama、vLLM等）
2. 在 `.env` 文件中添加：

```env
# 本地LLM配置
LOCAL_LLM_URL=http://localhost:11434/v1/chat/completions
LOCAL_LLM_MODEL=llama2
```

**优先级说明**：系统会按以下顺序尝试使用：
1. OpenAI（如果配置了 `OPENAI_API_KEY`）
2. Gemini（如果配置了 `GEMINI_API_KEY`）
3. Claude（如果配置了 `ANTHROPIC_API_KEY`）
4. 本地LLM（如果配置了 `LOCAL_LLM_URL`）

---

### 步骤2: 安装依赖

确保已安装AI相关的Python包：

```bash
pip install openai google-generativeai anthropic httpx jieba snownlp
```

或者使用项目的requirements.txt：

```bash
pip install -r requirements.txt
```

---

### 步骤3: 启动服务

#### 方法1: 使用一键启动脚本（推荐）

```bash
python 一键启动.py
```

#### 方法2: 手动启动

1. **启动Celery Worker**（用于异步分析任务）：
   ```bash
   celery -A app.tasks.celery_app worker --loglevel=info
   ```
   或使用批处理文件：`temp_start_celery.bat`

2. **启动FastAPI服务**：
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   或使用批处理文件：`启动FastAPI.bat`

---

### 步骤4: 使用AI分析功能

#### 方式1: 通过API接口（推荐）

**启动分析任务**：

```bash
POST http://localhost:8000/api/v1/brands/{brand_id}/analyze
Content-Type: application/json

{
  "analysis_type": "comprehensive",
  "include_sentiment": true,
  "include_topics": true,
  "include_keywords": true,
  "include_insights": true
}
```

**参数说明**：
- `brand_id`: 品牌ID（需要先创建品牌）
- `analysis_type`: 分析类型
  - `"comprehensive"` - 综合分析（推荐）
  - `"brand_image"` - 品牌形象分析
  - `"user_feedback"` - 用户反馈分析
  - `"trend"` - 趋势分析
- `include_sentiment`: 是否包含情感分析（默认：true）
- `include_topics`: 是否包含主题提取（默认：true）
- `include_keywords`: 是否包含关键词分析（默认：true）
- `include_insights`: 是否包含AI深度洞察（默认：true，需要配置LLM API）

**查看分析结果**：

```bash
GET http://localhost:8000/api/v1/brands/{brand_id}/analysis
```

#### 方式2: 通过Web界面

1. 访问API文档：http://localhost:8000/docs
2. 找到 `/api/v1/brands/{brand_id}/analyze` 接口
3. 点击 "Try it out"
4. 填写参数并执行
5. 使用 `/api/v1/brands/{brand_id}/analysis` 查看结果

#### 方式3: 使用数据分析界面

1. 访问：http://localhost:8000/api/v1/data-analysis
2. 选择平台和数据文件
3. 配置分析选项
4. 点击"开始分析"

---

## 📊 分析结果说明

分析完成后，结果包含以下部分：

### 1. 情感分析（Sentiment Analysis）

```json
{
  "sentiment": {
    "total": 100,
    "positive_count": 60,
    "negative_count": 20,
    "neutral_count": 20,
    "avg_score": 0.65,
    "distribution": {
      "positive": 60.0,
      "negative": 20.0,
      "neutral": 20.0
    }
  }
}
```

### 2. 关键词分析（Keywords）

```json
{
  "keywords": [
    {"keyword": "品牌名", "weight": 0.123},
    {"keyword": "关键词1", "weight": 0.098},
    ...
  ]
}
```

### 3. 文本统计（Text Statistics）

```json
{
  "text_statistics": {
    "total_count": 100,
    "total_length": 50000,
    "avg_length": 500.0,
    "word_frequency": [
      {"word": "词1", "count": 50},
      ...
    ]
  }
}
```

### 4. AI深度洞察（LLM Insights）

```json
{
  "llm_insights": {
    "analysis_type": "comprehensive",
    "insights": "AI生成的深度分析报告...",
    "model": "OpenAI-gpt-4"
  }
}
```

---

## 🔧 配置示例

### 完整配置示例（.env文件）

```env
# ===== 数据库配置 =====
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=brand_analysis

MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=brand_analysis

REDIS_HOST=localhost
REDIS_PORT=6379

# ===== AI配置（选择一种） =====
# 方式1: OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# 方式2: Claude（注释掉OpenAI配置，取消注释以下）
# ANTHROPIC_API_KEY=sk-ant-your-key-here
# ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# 方式3: 本地LLM（注释掉上述配置，取消注释以下）
# LOCAL_LLM_URL=http://localhost:11434/v1/chat/completions
# LOCAL_LLM_MODEL=llama2
```

---

## 💡 使用建议

### 1. 首次使用

- ✅ 先配置基础分析（情感、关键词），不需要LLM API
- ✅ 测试分析功能是否正常
- ✅ 再配置LLM API进行深度分析

### 2. 分析类型选择

- **综合分析**：适合首次分析，提供全面的品牌洞察
- **品牌形象分析**：专注于品牌定位和认知度
- **用户反馈分析**：专注于用户满意度和痛点
- **趋势分析**：专注于热度趋势和未来预测

### 3. 性能优化

- 数据量大时，分析可能需要几分钟
- 建议先爬取少量数据测试
- 使用Celery异步任务，不会阻塞API

### 4. 成本控制

- OpenAI按token计费，注意控制数据量
- 可以先用 `gpt-3.5-turbo` 测试（更便宜）
- 本地LLM无API费用，但需要硬件支持

---

## 🔍 常见问题

### Q1: 分析任务一直处于pending状态？

**A**: 检查Celery Worker是否正常运行：
```bash
# Windows PowerShell
Get-Process | Where-Object {$_.ProcessName -like "*celery*"}
```

### Q2: LLM分析失败，提示"未配置LLM API"？

**A**: 
1. 检查 `.env` 文件是否存在且配置正确
2. 确认API密钥格式正确（OpenAI以`sk-`开头，Claude以`sk-ant-`开头）
3. 重启FastAPI服务使配置生效

### Q3: OpenAI API调用失败？

**A**: 
1. 检查API密钥是否有效
2. 检查网络连接（可能需要代理）
3. 检查API配额是否充足
4. 如果使用代理服务，确认 `OPENAI_BASE_URL` 配置正确

### Q4: 如何查看分析任务的进度？

**A**: 
- 分析任务通过Celery异步执行
- 可以通过数据库查询任务状态：
  ```sql
  SELECT id, brand_id, status, progress, error_message 
  FROM analysis_tasks 
  WHERE brand_id = 1 
  ORDER BY created_at DESC;
  ```

### Q5: 分析结果存储在哪里？

**A**: 
- 分析结果存储在MongoDB的 `analysis_results` 集合中
- 可以通过API获取：`GET /api/v1/brands/{brand_id}/analysis`
- 也可以直接查询MongoDB

---

## 📝 完整使用示例

### 示例1: 使用Python脚本进行分析

```python
import requests

# 1. 创建品牌（如果还没有）
brand_data = {
    "name": "测试品牌",
    "description": "品牌描述",
    "keywords": ["关键词1", "关键词2"],
    "platforms": ["xhs", "douyin"]
}
response = requests.post("http://localhost:8000/api/v1/brands", json=brand_data)
brand_id = response.json()["data"]["id"]

# 2. 启动分析任务
analysis_data = {
    "analysis_type": "comprehensive",
    "include_sentiment": True,
    "include_keywords": True,
    "include_insights": True
}
response = requests.post(
    f"http://localhost:8000/api/v1/brands/{brand_id}/analyze",
    json=analysis_data
)
task_id = response.json()["data"]["task_id"]
print(f"分析任务已启动，任务ID: {task_id}")

# 3. 等待分析完成（实际使用中应该轮询查询）
import time
time.sleep(60)  # 等待60秒

# 4. 获取分析结果
response = requests.get(f"http://localhost:8000/api/v1/brands/{brand_id}/analysis")
result = response.json()
print("分析结果:", result)
```

### 示例2: 使用curl命令

```bash
# 启动分析任务
curl -X POST "http://localhost:8000/api/v1/brands/1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "comprehensive",
    "include_sentiment": true,
    "include_keywords": true,
    "include_insights": true
  }'

# 查看分析结果
curl "http://localhost:8000/api/v1/brands/1/analysis"
```

---

## ✅ 检查清单

在开始使用AI分析功能前，请确认：

- [ ] `.env` 文件已创建并配置了AI API密钥
- [ ] 已安装所有依赖：`pip install -r requirements.txt`
- [ ] MySQL数据库已启动并创建了数据库
- [ ] MongoDB已启动
- [ ] Redis已启动（Celery需要）
- [ ] Celery Worker已启动
- [ ] FastAPI服务已启动
- [ ] 已有爬取的数据可以分析（或先爬取数据）

---

## 📚 相关文档

- **数据分析使用说明**: `数据分析与AI分析使用说明.md`
- **API文档**: http://localhost:8000/docs
- **使用指南**: `docs/使用指南.md`

---

**现在你可以开始使用AI分析功能了！** 🎉

如有问题，请查看日志文件：`logs/app.log`

