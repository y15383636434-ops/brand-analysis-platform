# 品牌分析系统跨设备部署指南 (Deployment Guide)

本指南详细说明了如何将本品牌分析系统（包含 MediaCrawler 爬虫模块、FastAPI 后端、Celery 任务队列）完整迁移并部署到新的计算机环境中。

---

## 1. 环境准备 (Prerequisites)

在目标电脑上，请确保安装以下基础软件环境。建议使用 **Windows 10/11** 系统，因为项目包含针对 Windows 优化的启动脚本。

### 1.1 核心环境
1.  **Python 3.8 - 3.12**
    *   **重要**：请勿使用 Python 3.13（部分 AI 依赖库尚未兼容）。
    *   安装时务必勾选 "Add Python to PATH"（添加到环境变量）。
2.  **Node.js (LTS版本)**
    *   **必需**：MediaCrawler 爬虫模块部分核心加密算法依赖 Node.js 运行环境。
    *   下载地址：[Node.js 官网](https://nodejs.org/)
3.  **Google Chrome 浏览器**
    *   Playwright 爬虫默认依赖 Chrome/Chromium 进行自动化操作。

### 1.2 数据库与中间件
系统运行依赖以下服务，请确保安装并启动：
1.  **MySQL (8.0+)**: 
    *   用于存储业务数据、报表任务和分析结果。
    *   推荐安装 MySQL Workbench 或 Navicat 用于管理。
2.  **Redis (5.0+)**: 
    *   **必需**：用于 Celery 异步任务队列调度（爬虫任务分发）。
    *   Windows 用户可下载 [Redis for Windows](https://github.com/tporadowski/redis/releases)。

---

## 2. 部署步骤 (Deployment Steps)

### 2.1 获取代码
将项目文件夹 `githup` (或你的项目名) 完整复制到新电脑，或通过 Git 克隆。

### 2.2 创建 Python 虚拟环境
为了避免依赖冲突，建议使用虚拟环境：

```powershell
# 进入项目根目录
cd path/to/project

# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
# Windows Powershell:
.\venv\Scripts\activate
# Windows CMD:
.\venv\Scripts\activate.bat
# Linux/Mac:
source venv/bin/activate

# 激活成功后，命令行前缀会出现 (venv)
```

### 2.3 安装项目依赖
项目包含主程序依赖和爬虫子模块依赖，需分别安装。

```powershell
# 1. 安装主程序 Python 依赖
pip install -r requirements.txt

# 2. 安装 MediaCrawler 子模块 Python 依赖
pip install -r MediaCrawler/requirements.txt

# 3. 安装 MediaCrawler Node.js 依赖 (用于 JS 逆向)
cd MediaCrawler
npm install
cd ..

# 4. 安装 Playwright 浏览器驱动
playwright install
```

### 2.4 配置数据库与环境变量

1.  **创建数据库**：
    在 MySQL 中创建一个空的数据库，默认名称为 `brand_analysis`。
    ```sql
    CREATE DATABASE brand_analysis CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ```

2.  **修改配置**：
    打开项目根目录下的 `config.py` (或者复制 `.env.example` 为 `.env`)，修改以下关键配置：
    *   `MYSQL_PASSWORD`: 你的 MySQL 密码。
    *   `REDIS_HOST`: Redis 地址（默认 localhost）。
    *   `LLM_API_KEY`: (可选) 如果需要 AI 分析功能，填入你的 LLM 网关 Key。
    *   `MEDIACRAWLER_PATH`: 默认为 `./MediaCrawler`，通常无需修改。

3.  **初始化数据库表**：
    运行以下脚本自动创建数据表：
    ```powershell
    python scripts/init_database.py
    ```

---

## 3. 启动系统 (Startup)

确保 MySQL 和 Redis 服务已在后台运行。

### 方式 A：Windows 一键启动 (推荐)
在项目根目录下找到并双击运行：
👉 **`Start_System.bat`**

此脚本会自动：
1.  启动 Celery Worker (处理爬虫任务) - 弹出新窗口。
2.  启动 FastAPI (Web 服务) - 弹出新窗口。
3.  自动打开浏览器访问系统。

### 方式 B：手动启动 (Linux/Mac 或 调试用)
你需要打开两个终端窗口，并分别**激活虚拟环境**。

**窗口 1：启动 Celery 任务队列**
```powershell
# Windows (需加 -P solo)
celery -A app.tasks.celery_app worker --loglevel=info -P solo

# Linux/Mac
celery -A app.tasks.celery_app worker --loglevel=info
```

**窗口 2：启动 Web 服务**
```powershell
# 启动 API 服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

访问地址：
*   Web 界面: `http://localhost:8000`
*   API 文档: `http://localhost:8000/docs`

---

## 4. 常见问题 (Troubleshooting)

### Q1: `ModuleNotFoundError: No module named 'execjs'` 或 JS 执行报错
*   **原因**：缺少 PyExecJS 或 Node.js 环境。
*   **解决**：
    1. 确保安装了 Node.js (`node -v` 检查)。
    2. 确保安装了 pip 依赖 (`pip install PyExecJS`).

### Q2: 爬虫显示 "Browser closed" 或无法启动
*   **原因**：Playwright 未能找到浏览器。
*   **解决**：务必运行 `playwright install` 命令下载浏览器内核。

### Q3: 数据库连接失败 `Access denied`
*   **原因**：密码错误或权限不足。
*   **解决**：检查 `config.py` 中的 `MYSQL_PASSWORD`，并确保 MySQL 用户允许本地连接。

### Q4: Celery 报错 `ValueError: not enough values to unpack` (Windows)
*   **原因**：Windows 下 Celery 4.x+ 对多进程支持有问题。
*   **解决**：启动命令必须包含 `-P solo` 或 `-P gevent` 参数。

### Q5: 迁移后爬虫需要重新登录吗？
*   **是的**，除非你迁移了 `MediaCrawler/browser_data` 目录。
*   如果未迁移该目录，首次运行任务时，爬虫会自动弹出二维码，请扫描登录。登录成功后状态会被保存。
