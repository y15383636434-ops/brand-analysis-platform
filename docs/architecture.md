# 品牌分析系统 - 详细架构设计

## 1. 系统整体架构

### 1.1 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                        表示层 (Presentation)                  │
│  - Web前端 (React/Vue)                                        │
│  - 移动端 (可选)                                              │
└────────────────────┬──────────────────────────────────────────┘
                     │ HTTP/WebSocket
┌────────────────────▼──────────────────────────────────────────┐
│                     应用层 (Application)                      │
│  - FastAPI RESTful API                                        │
│  - WebSocket 实时通信                                         │
│  - 认证授权 (JWT)                                             │
└────────────────────┬──────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼───┐ ┌──────▼──────┐ ┌──▼──────────┐
│ 业务逻辑层 │ │  业务逻辑层  │ │ 业务逻辑层   │
│           │ │             │ │             │
│ 数据采集  │ │  AI分析     │ │ 报告生成    │
└───────┬───┘ └──────┬──────┘ └──┬──────────┘
        │            │            │
┌───────▼────────────▼────────────▼──────────┐
│              数据访问层 (Data Access)        │
│  - ORM (SQLAlchemy)                         │
│  - 数据清洗和转换                            │
└───────┬─────────────────────────────────────┘
        │
┌───────▼─────────────────────────────────────┐
│              数据存储层 (Storage)            │
│  - MySQL (品牌、任务、报告元数据)             │
│  - MongoDB (原始爬取数据、分析结果)          │
│  - Redis (缓存、任务队列)                    │
│  - 文件存储 (报告文件、图片)                 │
└─────────────────────────────────────────────┘
```

### 1.2 核心模块设计

#### 模块1: 数据采集服务 (Crawler Service)

**职责**：
- 管理多平台爬虫任务
- 调度和执行爬虫
- 数据清洗和存储

**技术实现**：
```python
# 伪代码示例
class CrawlerService:
    def __init__(self):
        self.mediacrawler = MediaCrawler()
        self.platforms = {
            'xhs': XHSCrawler(),
            'douyin': DouyinCrawler(),
            'weibo': WeiboCrawler(),
            'zhihu': ZhihuCrawler()
        }
    
    async def crawl_brand(self, brand_name: str, platforms: List[str]):
        """爬取品牌在各平台的数据"""
        tasks = []
        for platform in platforms:
            task = self._create_crawl_task(brand_name, platform)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return self._merge_results(results)
    
    def _create_crawl_task(self, brand_name: str, platform: str):
        """创建爬虫任务"""
        crawler = self.platforms[platform]
        return crawler.search(brand_name)
```

#### 模块2: AI分析服务 (Analysis Service)

**职责**：
- 调用大语言模型进行深度分析
- 执行情感分析、主题提取等NLP任务
- 生成分析洞察

**技术实现**：
```python
class AnalysisService:
    def __init__(self):
        self.llm_client = LLMClient()  # OpenAI/Claude/本地模型
        self.nlp_tools = NLPProcessor()
    
    async def analyze_brand(self, brand_id: int, data: Dict):
        """综合分析品牌数据"""
        # 1. 情感分析
        sentiment = await self._sentiment_analysis(data)
        
        # 2. 主题提取
        topics = await self._topic_extraction(data)
        
        # 3. 关键词分析
        keywords = await self._keyword_analysis(data)
        
        # 4. LLM深度分析
        insights = await self._llm_analysis(data, sentiment, topics)
        
        return {
            'sentiment': sentiment,
            'topics': topics,
            'keywords': keywords,
            'insights': insights
        }
    
    async def _llm_analysis(self, data: Dict, sentiment, topics):
        """使用LLM进行深度分析"""
        prompt = self._build_analysis_prompt(data, sentiment, topics)
        response = await self.llm_client.generate(prompt)
        return self._parse_llm_response(response)
```

#### 模块3: 报告生成服务 (Report Service)

**职责**：
- 根据分析结果生成报告
- 创建数据可视化图表
- 导出多种格式

**技术实现**：
```python
class ReportService:
    def __init__(self):
        self.template_engine = Jinja2Template()
        self.chart_generator = ChartGenerator()
    
    async def generate_report(self, brand_id: int, analysis_result: Dict):
        """生成品牌分析报告"""
        # 1. 准备报告数据
        report_data = self._prepare_report_data(brand_id, analysis_result)
        
        # 2. 生成图表
        charts = await self._generate_charts(analysis_result)
        
        # 3. 渲染报告模板
        html_report = self.template_engine.render('brand_report.html', {
            'data': report_data,
            'charts': charts
        })
        
        # 4. 转换为PDF
        pdf_report = self._html_to_pdf(html_report)
        
        return pdf_report
```

## 2. 数据流设计

### 2.1 数据采集流程

```
用户提交品牌 → API接收请求 → 创建爬虫任务 → 任务队列(Celery)
    ↓
执行爬虫任务 → 调用MediaCrawler → 获取原始数据
    ↓
数据清洗 → 去重、格式化 → 存储到数据库
    ↓
触发分析任务 → 通知AI分析服务
```

### 2.2 分析流程

```
接收分析任务 → 从数据库读取数据
    ↓
数据预处理 → 文本清洗、分词
    ↓
并行执行多个分析任务:
  - 情感分析 (NLP模型)
  - 主题提取 (LDA/BERT)
  - 关键词提取 (TF-IDF)
    ↓
LLM深度分析 → 生成洞察和建议
    ↓
存储分析结果 → MongoDB
    ↓
触发报告生成任务
```

### 2.3 报告生成流程

```
接收报告生成任务 → 读取分析结果
    ↓
数据可视化 → 生成图表(Matplotlib/ECharts)
    ↓
模板渲染 → Jinja2填充数据
    ↓
格式转换 → HTML → PDF/Word
    ↓
存储报告文件 → 文件系统/对象存储
    ↓
通知用户报告就绪
```

## 3. 数据库设计

### 3.1 MySQL 表结构

```sql
-- 品牌表
CREATE TABLE brands (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 爬虫任务表
CREATE TABLE crawl_tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    brand_id INT NOT NULL,
    platform VARCHAR(50) NOT NULL,
    status ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending',
    keyword VARCHAR(200),
    total_items INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (brand_id) REFERENCES brands(id)
);

-- 分析任务表
CREATE TABLE analysis_tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    brand_id INT NOT NULL,
    status ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending',
    analysis_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (brand_id) REFERENCES brands(id)
);

-- 报告表
CREATE TABLE reports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    brand_id INT NOT NULL,
    analysis_task_id INT,
    report_type VARCHAR(50),
    file_path VARCHAR(500),
    file_format VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands(id),
    FOREIGN KEY (analysis_task_id) REFERENCES analysis_tasks(id)
);
```

### 3.2 MongoDB 集合设计

```javascript
// 原始数据集合
{
  _id: ObjectId,
  brand_id: Number,
  platform: String,
  task_id: Number,
  content_type: String, // 'post', 'comment', 'video'
  content: String,
  author: String,
  publish_time: Date,
  engagement: {
    likes: Number,
    comments: Number,
    shares: Number
  },
  raw_data: Object,
  crawled_at: Date
}

// 分析结果集合
{
  _id: ObjectId,
  brand_id: Number,
  analysis_task_id: Number,
  sentiment_analysis: {
    positive: Number,
    negative: Number,
    neutral: Number,
    distribution: Array
  },
  topics: Array,
  keywords: Array,
  insights: String,
  trends: Object,
  created_at: Date
}
```

## 4. API设计

### 4.1 RESTful API 端点

```
# 品牌管理
POST   /api/v1/brands              # 创建品牌
GET    /api/v1/brands              # 获取品牌列表
GET    /api/v1/brands/{id}         # 获取品牌详情
PUT    /api/v1/brands/{id}         # 更新品牌
DELETE /api/v1/brands/{id}         # 删除品牌

# 数据采集
POST   /api/v1/brands/{id}/crawl   # 启动爬虫任务
GET    /api/v1/crawl-tasks         # 获取任务列表
GET    /api/v1/crawl-tasks/{id}    # 获取任务详情

# 数据分析
POST   /api/v1/brands/{id}/analyze # 启动分析任务
GET    /api/v1/analysis-tasks      # 获取分析任务列表
GET    /api/v1/brands/{id}/analysis # 获取分析结果

# 报告生成
POST   /api/v1/brands/{id}/reports # 生成报告
GET    /api/v1/reports             # 获取报告列表
GET    /api/v1/reports/{id}        # 下载报告
```

### 4.2 WebSocket 实时通信

```javascript
// 任务状态更新
ws://api/v1/tasks/{task_id}/stream

// 消息格式
{
  "type": "task_update",
  "task_id": 123,
  "status": "running",
  "progress": 45,
  "message": "正在分析数据..."
}
```

## 5. 技术选型说明

### 5.1 为什么选择 FastAPI？
- 异步支持，适合I/O密集型任务
- 自动生成API文档
- 类型提示支持
- 性能优秀

### 5.2 为什么选择 Celery？
- 异步任务处理
- 支持任务队列和调度
- 可扩展性强
- 适合长时间运行的任务

### 5.3 为什么选择 MongoDB？
- 存储非结构化数据（原始爬取内容）
- 灵活的schema
- 适合存储大量文本数据

### 5.4 AI模型选择
- **情感分析**：使用预训练的中文情感分析模型（如bert-base-chinese）
- **主题提取**：LDA或BERT-based主题模型
- **深度分析**：OpenAI GPT-4 / Claude / 本地LLM（如ChatGLM）

## 6. 部署架构

### 6.1 容器化部署

```yaml
# docker-compose.yml 示例
services:
  api:
    image: brand-analysis-api
    ports:
      - "8000:8000"
  
  worker:
    image: brand-analysis-worker
    depends_on:
      - redis
      - mysql
      - mongodb
  
  redis:
    image: redis:alpine
  
  mysql:
    image: mysql:8.0
  
  mongodb:
    image: mongo:latest
  
  frontend:
    image: brand-analysis-frontend
    ports:
      - "3000:3000"
```

### 6.2 扩展性考虑
- 水平扩展：多个worker节点处理任务
- 负载均衡：Nginx反向代理
- 缓存策略：Redis缓存热点数据
- 数据库分片：MongoDB分片存储大量数据

