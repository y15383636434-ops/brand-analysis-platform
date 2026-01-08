# 🚀 Gemini 3 Pro 快速配置指南

## ✅ 已完成的配置

1. ✅ 已安装 `google-generativeai` 包
2. ✅ 已更新代码支持 Gemini API
3. ✅ 已更新配置文件添加 Gemini 配置项

## 📝 需要您手动完成的步骤

### 步骤1: 创建 .env 文件

在项目根目录（`C:\Users\Yu\cursorProjects\githup\`）创建 `.env` 文件，并添加以下内容：

```env
# ===== 数据库配置 =====
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root123456
MYSQL_DATABASE=brand_analysis

MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=brand_analysis

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# ===== Celery配置 =====
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# ===== AI配置 - Gemini 3 Pro =====
GEMINI_API_KEY=sk-gwCyORqv81gZ9Vi38pcPfNfhfv87bIzHVAqyPm5kNgufmpTn
GEMINI_MODEL=gemini-2.0-flash-exp

# ===== 安全配置 =====
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ===== 日志配置 =====
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# ===== MediaCrawler配置 =====
MEDIACRAWLER_PATH=./MediaCrawler
MEDIACRAWLER_PYTHON=

USE_REAL_CRAWLER=True
FORCE_REAL_CRAWL=True

# ===== 爬虫配置 =====
CRAWL_MAX_ITEMS=100
CRAWL_INCLUDE_COMMENTS=True
CRAWL_TIMEOUT=300
```

**重要**：请将您的 Gemini API 密钥替换到 `GEMINI_API_KEY` 的值中。

### 步骤2: 验证配置

运行配置检查脚本：

```bash
python check_ai_config.py
```

如果配置正确，您应该看到：

```
[OK] Gemini配置已设置
   API Key: sk-gwCyORq...
   Model: gemini-2.0-flash-exp
   [使用] 将使用 Gemini 进行AI分析
```

### 步骤3: 测试AI分析功能

1. **启动服务**：
   
   ```bash
   # 启动Celery Worker
   celery -A app.tasks.celery_app worker --loglevel=info
   
   # 启动FastAPI（另一个终端）
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **访问API文档**：
   打开浏览器访问：http://localhost:8000/docs

3. **启动分析任务**：
   
   ```bash
   POST /api/v1/brands/{brand_id}/analyze
   {
     "analysis_type": "comprehensive",
     "include_sentiment": true,
     "include_keywords": true,
     "include_insights": true
   }
   ```

## 📋 配置说明

### Gemini 模型选择

您可以在 `.env` 文件中修改 `GEMINI_MODEL` 来使用不同的模型：

- `gemini-2.0-flash-exp` - 最新实验版本（推荐）
- `gemini-1.5-pro` - 专业版，性能更强
- `gemini-1.5-flash` - 快速版本，响应更快

### API优先级

系统会按以下顺序尝试使用AI服务：

1. OpenAI（如果配置了 `OPENAI_API_KEY`）
2. **Gemini（如果配置了 `GEMINI_API_KEY`）** ← 您当前使用这个
3. Claude（如果配置了 `ANTHROPIC_API_KEY`）
4. 本地LLM（如果配置了 `LOCAL_LLM_URL`）

## ⚠️ 注意事项

1. **API密钥安全**：
   
   - 不要将 `.env` 文件提交到Git仓库
   - `.env` 文件已在 `.gitignore` 中，不会被提交

2. **API限制**：
   
   - Gemini API有免费额度限制
   - 注意控制调用频率，避免超出限制

3. **网络访问**：
   
   - 确保可以访问 Google API 服务
   - 如果在中国大陆，可能需要配置代理

## 🔍 故障排查

### 问题1: 配置检查显示"未找到 .env 文件"

**解决方案**：

- 确认 `.env` 文件在项目根目录
- 确认文件名是 `.env`（不是 `.env.txt`）

### 问题2: Gemini API调用失败

**检查项**：

1. API密钥是否正确
2. 网络连接是否正常
3. API配额是否充足
4. 查看日志文件：`logs/app.log`

### 问题3: 依赖包未安装

**解决方案**：

```bash
pip install google-generativeai
```

## 📚 相关文档

- **完整AI分析指南**: `AI分析接入指南.md`
- **API文档**: http://localhost:8000/docs
- **配置模板**: `env_template.txt`

---

**配置完成后，您就可以开始使用 Gemini 3 Pro 进行AI分析了！** 🎉



