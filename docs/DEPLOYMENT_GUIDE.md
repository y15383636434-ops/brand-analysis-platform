# 项目跨设备部署指南 (Deployment Guide)

本指南详细说明了如何将本品牌分析系统（包含 MediaCrawler 爬虫模块）迁移并部署到新的计算机环境中。

## 1. 环境准备 (Prerequisites)

在目标电脑上，请确保安装以下基础软件环境：

### 1.1 操作系统
*   推荐：**Windows 10/11** (已包含 `.bat` 启动脚本)
*   支持：Linux / macOS (需手动运行 Shell 命令)

### 1.2 核心软件
请按照以下顺序安装：
1.  **Python 3.8 - 3.11**
    *   注意：暂不推荐 Python 3.13（部分 AI 库兼容性问题）。
    *   安装时请勾选 "Add Python to PATH"。
2.  **Google Chrome 浏览器**
    *   Playwright 爬虫依赖 Chrome 进行自动化操作。
3.  **Git** (可选，用于拉取代码)

### 1.3 数据库与中间件
系统运行需要以下服务支持，请确保服务已安装并启动：
1.  **MySQL (8.0+)**: 存储业务数据、报表和用户信息。
2.  **Redis**: 用于 Celery 任务队列调度和缓存。
3.  **MongoDB**: 存储爬虫抓取的非结构化原始数据。

---

## 2. 文件与数据迁移 (Migration)

### 2.1 代码文件
将项目根目录 `githup/` 下的所有文件复制到目标电脑。

**⚠️ 重要提示：保留爬虫登录状态**
如果您希望在新电脑上直接使用爬虫，而**无需重新扫码登录**各平台账号，请务必完整复制以下目录：
*   `MediaCrawler/browser_data/` 
*   该目录包含了浏览器指纹、Cookies 和 LocalStorage 数据。

### 2.2 数据迁移 (可选)
如果您需要保留旧电脑上的历史数据：
1.  **MySQL**: 导出 `brand_analysis` 数据库为 SQL 文件，在新电脑导入。
2.  **MongoDB**: 导出 `brand_analysis` 数据库，在新电脑恢复。

---

## 3. 安装部署 (Installation)

在目标电脑的项目根目录下，打开终端（CMD 或 PowerShell）执行以下步骤：

### 3.1 创建虚拟环境
隔离项目环境，避免污染全局 Python 库。
```powershell
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
.\venv\Scripts\activate
# 激活成功后，命令行前会出现 (venv) 提示
```

### 3.2 安装依赖库
```powershell
# 1. 安装主项目依赖
pip install -r requirements.txt

# 2. 安装爬虫模块依赖 (确保在 MediaCrawler 目录下也有相关依赖)
# 如果 MediaCrawler 目录下有 requirements.txt:
pip install -r MediaCrawler/requirements.txt
```

### 3.3 安装浏览器驱动
```powershell
playwright install
```

---

## 4. 系统配置 (Configuration)

找到项目根目录下的 `config.py` (或 `.env` 文件)，根据新环境修改配置。

### 4.1 数据库配置
```python
# 修改为新电脑的数据库密码
MYSQL_PASSWORD = "your_new_password"

# 如果数据库不在本地，修改 IP 地址
MYSQL_HOST = "localhost" 
REDIS_HOST = "localhost"
MONGODB_HOST = "localhost"
```

### 4.2 数据库初始化 (仅限全新部署)
如果未迁移旧数据，需要初始化数据库表结构：
```powershell
python scripts/init_database.py
```

---

## 5. 启动运行 (Startup)

确保 MySQL、Redis、MongoDB 服务已运行。

### 方式 A：Windows 一键启动 (推荐)
双击运行根目录下的脚本：
*   **`Start_System.bat`**

### 方式 B：手动启动
需要打开两个命令行窗口（均需先激活 `venv`）：

**窗口 1：Web 服务 (FastAPI)**
```powershell
python run.py
```
*访问地址: http://localhost:8000*

**窗口 2：任务队列 (Celery)**
```powershell
# Windows 下必须添加 -P solo 参数
celery -A tasks.celery_app worker --loglevel=info -P solo
```

---

## 6. 常见问题排查 (Troubleshooting)

### Q1: 运行 `pip install` 报错？
*   检查是否升级了 pip: `python -m pip install --upgrade pip`
*   检查网络是否通畅，尝试切换国内源: `-i https://pypi.tuna.tsinghua.edu.cn/simple`

### Q2: 爬虫启动失败或报错 "Browser closed"？
*   确保已运行 `playwright install`。
*   Windows Server 版本可能缺少多媒体组件，需安装 "Desktop Experience" 或相关补丁。

### Q3: Celery 任务不执行？
*   检查 Redis 服务是否启动。
*   Windows 环境下确认启动命令包含了 `-P solo` 或 `-P gevent`。

### Q4: 端口被占用 (Port in use)？
*   默认端口：API(8000), MySQL(3306), Redis(6379)。
*   修改 `config.py` 中的 `PORT` 设置，或关闭占用端口的程序。
