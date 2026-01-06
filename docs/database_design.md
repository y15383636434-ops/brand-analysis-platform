# 数据库设计文档

## 1. MySQL 数据库设计

### 1.1 品牌表 (brands)

存储品牌基本信息。

```sql
CREATE TABLE brands (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '品牌ID',
    name VARCHAR(100) NOT NULL COMMENT '品牌名称',
    description TEXT COMMENT '品牌描述',
    keywords JSON COMMENT '关键词列表，JSON格式',
    platforms JSON COMMENT '支持的平台列表，JSON格式',
    status ENUM('active', 'inactive', 'archived') DEFAULT 'active' COMMENT '状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_name (name),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='品牌表';
```

**示例数据**:
```json
{
  "id": 1,
  "name": "山四砂锅",
  "description": "传统砂锅品牌",
  "keywords": ["山四砂锅", "山四", "砂锅"],
  "platforms": ["xhs", "douyin", "weibo", "zhihu"],
  "status": "active"
}
```

### 1.2 爬虫任务表 (crawl_tasks)

存储爬虫任务信息。

```sql
CREATE TABLE crawl_tasks (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '任务ID',
    brand_id INT NOT NULL COMMENT '品牌ID',
    platform VARCHAR(50) NOT NULL COMMENT '平台名称',
    status ENUM('pending', 'running', 'completed', 'failed', 'cancelled') 
        DEFAULT 'pending' COMMENT '任务状态',
    keyword VARCHAR(200) COMMENT '搜索关键词',
    max_items INT DEFAULT 100 COMMENT '最大采集数量',
    total_items INT DEFAULT 0 COMMENT '总数据量',
    crawled_items INT DEFAULT 0 COMMENT '已采集数量',
    failed_items INT DEFAULT 0 COMMENT '失败数量',
    progress INT DEFAULT 0 COMMENT '进度百分比 0-100',
    error_message TEXT COMMENT '错误信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    started_at TIMESTAMP NULL COMMENT '开始时间',
    completed_at TIMESTAMP NULL COMMENT '完成时间',
    duration INT COMMENT '耗时（秒）',
    
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
    INDEX idx_brand_id (brand_id),
    INDEX idx_platform (platform),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='爬虫任务表';
```

### 1.3 分析任务表 (analysis_tasks)

存储AI分析任务信息。

```sql
CREATE TABLE analysis_tasks (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '任务ID',
    brand_id INT NOT NULL COMMENT '品牌ID',
    status ENUM('pending', 'running', 'completed', 'failed', 'cancelled') 
        DEFAULT 'pending' COMMENT '任务状态',
    analysis_type VARCHAR(50) DEFAULT 'full' COMMENT '分析类型',
    include_sentiment BOOLEAN DEFAULT TRUE COMMENT '包含情感分析',
    include_topics BOOLEAN DEFAULT TRUE COMMENT '包含主题提取',
    include_keywords BOOLEAN DEFAULT TRUE COMMENT '包含关键词分析',
    include_insights BOOLEAN DEFAULT TRUE COMMENT '包含深度洞察',
    progress INT DEFAULT 0 COMMENT '进度百分比 0-100',
    error_message TEXT COMMENT '错误信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    started_at TIMESTAMP NULL COMMENT '开始时间',
    completed_at TIMESTAMP NULL COMMENT '完成时间',
    duration INT COMMENT '耗时（秒）',
    
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
    INDEX idx_brand_id (brand_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分析任务表';
```

### 1.4 报告表 (reports)

存储生成的报告信息。

```sql
CREATE TABLE reports (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '报告ID',
    brand_id INT NOT NULL COMMENT '品牌ID',
    analysis_task_id INT COMMENT '关联的分析任务ID',
    report_type VARCHAR(50) DEFAULT 'full' COMMENT '报告类型',
    format VARCHAR(20) DEFAULT 'pdf' COMMENT '文件格式',
    file_path VARCHAR(500) COMMENT '文件路径',
    file_size BIGINT COMMENT '文件大小（字节）',
    file_url VARCHAR(500) COMMENT '文件访问URL',
    language VARCHAR(10) DEFAULT 'zh-CN' COMMENT '语言',
    status ENUM('generating', 'completed', 'failed') DEFAULT 'generating' COMMENT '状态',
    error_message TEXT COMMENT '错误信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    completed_at TIMESTAMP NULL COMMENT '完成时间',
    
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
    FOREIGN KEY (analysis_task_id) REFERENCES analysis_tasks(id) ON DELETE SET NULL,
    INDEX idx_brand_id (brand_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报告表';
```

### 1.5 数据统计表 (brand_stats)

存储品牌的统计数据（可选，用于快速查询）。

```sql
CREATE TABLE brand_stats (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
    brand_id INT NOT NULL COMMENT '品牌ID',
    platform VARCHAR(50) COMMENT '平台名称，NULL表示全部平台',
    total_posts INT DEFAULT 0 COMMENT '总帖子数',
    total_comments INT DEFAULT 0 COMMENT '总评论数',
    total_videos INT DEFAULT 0 COMMENT '总视频数',
    last_crawl_time TIMESTAMP NULL COMMENT '最后爬取时间',
    last_analysis_time TIMESTAMP NULL COMMENT '最后分析时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
    UNIQUE KEY uk_brand_platform (brand_id, platform),
    INDEX idx_brand_id (brand_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='品牌统计表';
```

## 2. MongoDB 集合设计

### 2.1 原始数据集合 (raw_data)

存储从各平台爬取的原始数据。

```javascript
{
  _id: ObjectId,
  brand_id: Number,           // 品牌ID
  platform: String,            // 平台: xhs, douyin, weibo, zhihu
  task_id: Number,             // 爬虫任务ID
  content_type: String,        // 内容类型: post, comment, video
  content_id: String,          // 平台上的内容ID
  
  // 内容信息
  title: String,               // 标题
  content: String,             // 正文内容
  author: {                     // 作者信息
    id: String,
    name: String,
    avatar: String
  },
  publish_time: Date,          // 发布时间
  
  // 互动数据
  engagement: {
    likes: Number,
    comments: Number,
    shares: Number,
    views: Number
  },
  
  // 媒体信息
  media: {
    images: [String],          // 图片URL列表
    videos: [String]           // 视频URL列表
  },
  
  // 原始数据（完整JSON）
  raw_data: Object,
  
  // 元数据
  crawled_at: Date,           // 爬取时间
  updated_at: Date             // 更新时间
}
```

**索引**:
```javascript
db.raw_data.createIndex({ brand_id: 1, platform: 1, publish_time: -1 });
db.raw_data.createIndex({ task_id: 1 });
db.raw_data.createIndex({ content_id: 1, platform: 1 }, { unique: true });
```

### 2.2 分析结果集合 (analysis_results)

存储AI分析的结果。

```javascript
{
  _id: ObjectId,
  brand_id: Number,            // 品牌ID
  analysis_task_id: Number,    // 分析任务ID
  
  // 情感分析结果
  sentiment_analysis: {
    positive: Number,          // 正面比例
    negative: Number,          // 负面比例
    neutral: Number,           // 中性比例
    total_samples: Number,     // 样本总数
    distribution: [            // 时间分布
      {
        date: String,
        positive: Number,
        negative: Number,
        neutral: Number
      }
    ],
    by_platform: {             // 按平台分布
      xhs: { positive: Number, negative: Number, neutral: Number },
      douyin: { ... },
      weibo: { ... }
    }
  },
  
  // 主题分析结果
  topics: [
    {
      topic: String,           // 主题名称
      weight: Number,          // 权重
      keywords: [String],      // 关键词
      sample_count: Number,    // 样本数量
      sentiment: {             // 该主题的情感分布
        positive: Number,
        negative: Number,
        neutral: Number
      }
    }
  ],
  
  // 关键词分析结果
  keywords: [
    {
      word: String,            // 关键词
      frequency: Number,       // 频次
      weight: Number,          // 权重（TF-IDF）
      sentiment: String        // 情感倾向: positive/negative/neutral
    }
  ],
  
  // 趋势分析
  trends: {
    mention_count: [Number],   // 提及次数趋势
    dates: [String],           // 对应日期
    engagement_trend: [Number], // 互动量趋势
    sentiment_trend: [Number]   // 情感趋势
  },
  
  // LLM生成的深度洞察
  insights: {
    summary: String,           // 总结
    strengths: [String],       // 优势
    weaknesses: [String],      // 劣势
    opportunities: [String],   // 机会
    threats: [String],         // 威胁
    recommendations: [String]  // 建议
  },
  
  // 元数据
  generated_at: Date,         // 生成时间
  data_range: {                // 数据范围
    start_date: Date,
    end_date: Date,
    total_items: Number
  }
}
```

**索引**:
```javascript
db.analysis_results.createIndex({ brand_id: 1, generated_at: -1 });
db.analysis_results.createIndex({ analysis_task_id: 1 }, { unique: true });
```

### 2.3 数据缓存集合 (cache)

存储临时数据和缓存。

```javascript
{
  _id: ObjectId,
  key: String,                 // 缓存键
  value: Object,               // 缓存值
  expires_at: Date,           // 过期时间
  created_at: Date            // 创建时间
}
```

**索引**:
```javascript
db.cache.createIndex({ key: 1 }, { unique: true });
db.cache.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 });
```

## 3. Redis 数据结构

### 3.1 任务队列

使用Redis List存储待处理的任务。

```
Key: task_queue:crawl
Type: List
Value: JSON字符串，包含任务信息

Key: task_queue:analyze
Type: List
Value: JSON字符串，包含任务信息
```

### 3.2 任务状态

使用Redis Hash存储任务实时状态。

```
Key: task:status:{task_id}
Type: Hash
Fields:
  - status: 任务状态
  - progress: 进度
  - message: 消息
  - updated_at: 更新时间
```

### 3.3 缓存

使用Redis String存储热点数据。

```
Key: brand:{brand_id}:stats
Type: String (JSON)
TTL: 3600秒

Key: analysis:{brand_id}:latest
Type: String (JSON)
TTL: 1800秒
```

## 4. 数据库关系图

```
brands (1) ──< (N) crawl_tasks
brands (1) ──< (N) analysis_tasks
brands (1) ──< (N) reports
brands (1) ──< (N) brand_stats

analysis_tasks (1) ──< (N) reports

MongoDB:
  raw_data.brand_id → brands.id
  analysis_results.brand_id → brands.id
  analysis_results.analysis_task_id → analysis_tasks.id
```

## 5. 数据迁移脚本示例

```python
# migrations/001_create_tables.py
from sqlalchemy import create_engine, text

def upgrade():
    engine = create_engine('mysql://user:pass@localhost/dbname')
    with engine.connect() as conn:
        # 创建brands表
        conn.execute(text("""
            CREATE TABLE brands (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                ...
            )
        """))
        conn.commit()

def downgrade():
    # 回滚操作
    pass
```

## 6. 数据备份策略

1. **MySQL备份**: 每日全量备份 + 每小时增量备份
2. **MongoDB备份**: 每日全量备份
3. **Redis备份**: 定期RDB快照
4. **文件备份**: 报告文件定期备份到对象存储

