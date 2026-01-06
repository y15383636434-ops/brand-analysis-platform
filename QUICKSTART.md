# 🚀 快速开始指南

## 5分钟快速上手

### 步骤1: 安装依赖

```bash
pip install -r requirements.txt
```

### 步骤2: 配置数据库

1. 确保MySQL、MongoDB、Redis已安装并运行
2. 修改 `config.py` 中的数据库配置
3. 运行数据库初始化脚本：

```bash
python scripts/init_database.py
```

### 步骤3: 启动服务

**方式1: 一键启动（推荐）**
```bash
python 一键启动.py
```

**方式2: 批处理文件**
```bash
start.bat
```

**方式3: 手动启动**
- 打开第一个命令行窗口：`启动Celery.bat`
- 打开第二个命令行窗口：`启动FastAPI.bat`

### 步骤4: 访问API文档

打开浏览器访问：**http://localhost:8000/docs**

### 步骤5: 快速测试

运行快速开始示例：

```bash
python 快速开始示例.py
```

---

## 📋 基本使用流程

### 1. 创建品牌

```bash
POST /api/v1/brands
{
  "name": "测试品牌",
  "keywords": ["关键词"],
  "platforms": ["xhs", "douyin"]
}
```

### 2. 创建爬虫任务

```bash
POST /api/v1/brands/1/crawl-tasks
{
  "platform": "xhs",
  "keyword": "测试关键词",
  "max_items": 10
}
```

### 3. 查看任务状态

```bash
GET /api/v1/crawl-tasks/{task_id}
```

### 4. 查看爬取数据

```bash
GET /api/v1/brands/1/data/stats
GET /api/v1/brands/1/data
```

---

## 🔧 配置说明

### 数据库配置

编辑 `config.py` 或创建 `.env` 文件：

```python
MYSQL_PASSWORD = "your_password"
MONGODB_HOST = "localhost"
REDIS_HOST = "localhost"
```

### MediaCrawler配置

```python
USE_REAL_CRAWLER = True  # 使用真实爬虫
MEDIACRAWLER_PATH = "./MediaCrawler"
```

---

## ⚠️ 常见问题

### 端口8000被占用？

运行端口释放脚本：
```bash
python free_port_8000.py
```

### 服务无法启动？

1. 检查数据库是否运行
2. 检查端口是否被占用
3. 查看日志文件：`logs/app.log`

### MediaCrawler无法使用？

运行检查脚本：
```bash
python check_real_crawler.py
```

---

## 📚 更多文档

- **完整使用指南**: `docs/使用指南.md`
- **MediaCrawler使用**: `MediaCrawler使用指南.md`
- **项目结构**: `项目结构说明.md`
- **API文档**: http://localhost:8000/docs

---

**现在就可以开始使用了！** 🎉





