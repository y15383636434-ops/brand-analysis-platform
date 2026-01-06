# API接口设计文档

## API基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **认证方式**: JWT Token (可选)
- **数据格式**: JSON
- **字符编码**: UTF-8

## 1. 品牌管理 API

### 1.1 创建品牌

**请求**
```http
POST /api/v1/brands
Content-Type: application/json

{
  "name": "山四砂锅",
  "description": "传统砂锅品牌",
  "keywords": ["山四砂锅", "山四", "砂锅"],
  "platforms": ["xhs", "douyin", "weibo", "zhihu"]
}
```

**响应**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "name": "山四砂锅",
    "description": "传统砂锅品牌",
    "keywords": ["山四砂锅", "山四", "砂锅"],
    "platforms": ["xhs", "douyin", "weibo", "zhihu"],
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z"
  }
}
```

### 1.2 获取品牌列表

**请求**
```http
GET /api/v1/brands?page=1&page_size=10
```

**响应**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "山四砂锅",
        "description": "传统砂锅品牌",
        "created_at": "2024-01-15T10:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 10
  }
}
```

### 1.3 获取品牌详情

**请求**
```http
GET /api/v1/brands/1
```

**响应**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "name": "山四砂锅",
    "description": "传统砂锅品牌",
    "keywords": ["山四砂锅", "山四", "砂锅"],
    "platforms": ["xhs", "douyin", "weibo", "zhihu"],
    "stats": {
      "total_posts": 1250,
      "total_comments": 5600,
      "last_crawl_time": "2024-01-15T09:00:00Z",
      "last_analysis_time": "2024-01-15T09:30:00Z"
    },
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z"
  }
}
```

## 2. 数据采集 API

### 2.1 启动爬虫任务

**请求**
```http
POST /api/v1/brands/1/crawl
Content-Type: application/json

{
  "platforms": ["xhs", "douyin"],
  "keywords": ["山四砂锅"],
  "max_items": 100,
  "include_comments": true
}
```

**响应**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "task_id": 123,
    "brand_id": 1,
    "platforms": ["xhs", "douyin"],
    "status": "pending",
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

### 2.2 获取爬虫任务列表

**请求**
```http
GET /api/v1/crawl-tasks?brand_id=1&status=running&page=1
```

**响应**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 123,
        "brand_id": 1,
        "platform": "xhs",
        "status": "running",
        "progress": 45,
        "total_items": 100,
        "crawled_items": 45,
        "created_at": "2024-01-15T10:00:00Z",
        "started_at": "2024-01-15T10:01:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 10
  }
}
```

### 2.3 获取爬虫任务详情

**请求**
```http
GET /api/v1/crawl-tasks/123
```

**响应**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 123,
    "brand_id": 1,
    "platform": "xhs",
    "status": "completed",
    "progress": 100,
    "total_items": 100,
    "crawled_items": 100,
    "keyword": "山四砂锅",
    "created_at": "2024-01-15T10:00:00Z",
    "started_at": "2024-01-15T10:01:00Z",
    "completed_at": "2024-01-15T10:15:00Z",
    "duration": 840
  }
}
```

## 3. 数据分析 API

### 3.1 启动分析任务

**请求**
```http
POST /api/v1/brands/1/analyze
Content-Type: application/json

{
  "analysis_type": "full",
  "include_sentiment": true,
  "include_topics": true,
  "include_keywords": true,
  "include_insights": true
}
```

**响应**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "task_id": 456,
    "brand_id": 1,
    "analysis_type": "full",
    "status": "pending",
    "created_at": "2024-01-15T10:20:00Z"
  }
}
```

### 3.2 获取分析结果

**请求**
```http
GET /api/v1/brands/1/analysis
```

**响应**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "brand_id": 1,
    "analysis_task_id": 456,
    "generated_at": "2024-01-15T10:25:00Z",
    "sentiment_analysis": {
      "positive": 65.5,
      "negative": 15.2,
      "neutral": 19.3,
      "total_samples": 1250,
      "distribution": [
        {"date": "2024-01-01", "positive": 60, "negative": 20, "neutral": 20},
        {"date": "2024-01-15", "positive": 70, "negative": 10, "neutral": 20}
      ]
    },
    "topics": [
      {
        "topic": "产品质量",
        "weight": 0.35,
        "keywords": ["质量", "好用", "耐用"],
        "sample_count": 450
      },
      {
        "topic": "价格",
        "weight": 0.25,
        "keywords": ["价格", "性价比", "便宜"],
        "sample_count": 320
      }
    ],
    "keywords": [
      {"word": "砂锅", "frequency": 850, "weight": 0.68},
      {"word": "质量", "frequency": 450, "weight": 0.36},
      {"word": "好用", "frequency": 320, "weight": 0.26}
    ],
    "insights": "根据分析，山四砂锅品牌在社交媒体上的整体口碑较好...",
    "trends": {
      "mention_count": [100, 120, 150, 180, 200],
      "dates": ["2024-01-01", "2024-01-05", "2024-01-10", "2024-01-12", "2024-01-15"]
    }
  }
}
```

## 4. 报告生成 API

### 4.1 生成报告

**请求**
```http
POST /api/v1/brands/1/reports
Content-Type: application/json

{
  "report_type": "full",
  "format": "pdf",
  "include_charts": true,
  "language": "zh-CN"
}
```

**响应**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "report_id": 789,
    "brand_id": 1,
    "report_type": "full",
    "format": "pdf",
    "status": "generating",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### 4.2 获取报告列表

**请求**
```http
GET /api/v1/reports?brand_id=1&page=1
```

**响应**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 789,
        "brand_id": 1,
        "brand_name": "山四砂锅",
        "report_type": "full",
        "format": "pdf",
        "file_size": 2048576,
        "created_at": "2024-01-15T10:30:00Z",
        "download_url": "/api/v1/reports/789/download"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 10
  }
}
```

### 4.3 下载报告

**请求**
```http
GET /api/v1/reports/789/download
```

**响应**
- Content-Type: application/pdf (或其他格式)
- Content-Disposition: attachment; filename="brand_report_1_20240115.pdf"
- 文件流

## 5. WebSocket 实时通信

### 5.1 连接WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/tasks/123/stream');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('任务更新:', data);
};
```

### 5.2 消息格式

**任务状态更新**
```json
{
  "type": "task_update",
  "task_id": 123,
  "task_type": "crawl",
  "status": "running",
  "progress": 45,
  "message": "正在爬取小红书数据...",
  "timestamp": "2024-01-15T10:05:00Z"
}
```

**任务完成**
```json
{
  "type": "task_completed",
  "task_id": 123,
  "task_type": "crawl",
  "status": "completed",
  "result": {
    "total_items": 100,
    "success_items": 98,
    "failed_items": 2
  },
  "timestamp": "2024-01-15T10:15:00Z"
}
```

**任务失败**
```json
{
  "type": "task_failed",
  "task_id": 123,
  "task_type": "crawl",
  "status": "failed",
  "error": "网络连接超时",
  "timestamp": "2024-01-15T10:10:00Z"
}
```

## 6. 错误响应格式

所有错误响应都遵循统一格式：

```json
{
  "code": 400,
  "message": "请求参数错误",
  "error": {
    "field": "platforms",
    "message": "platforms字段不能为空"
  }
}
```

### 常见错误码

- `200`: 成功
- `400`: 请求参数错误
- `401`: 未授权
- `404`: 资源不存在
- `500`: 服务器内部错误
- `503`: 服务不可用

## 7. 数据模型

### Brand (品牌)
```python
class Brand(BaseModel):
    id: int
    name: str
    description: Optional[str]
    keywords: List[str]
    platforms: List[str]
    created_at: datetime
    updated_at: datetime
```

### CrawlTask (爬虫任务)
```python
class CrawlTask(BaseModel):
    id: int
    brand_id: int
    platform: str
    status: str  # pending, running, completed, failed
    keyword: str
    total_items: int
    crawled_items: int
    progress: int  # 0-100
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
```

### AnalysisResult (分析结果)
```python
class AnalysisResult(BaseModel):
    brand_id: int
    sentiment_analysis: SentimentAnalysis
    topics: List[Topic]
    keywords: List[Keyword]
    insights: str
    trends: TrendData
    generated_at: datetime
```

