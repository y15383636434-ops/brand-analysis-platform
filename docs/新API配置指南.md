# 新API配置指南

本指南将帮助您快速添加新的API端点到品牌分析系统中。

## 📋 目录

1. [快速开始](#快速开始)
2. [API文件结构](#api文件结构)
3. [创建新API的步骤](#创建新api的步骤)
4. [API开发规范](#api开发规范)
5. [示例：创建一个新的API模块](#示例创建一个新的api模块)
6. [常见问题](#常见问题)

---

## 快速开始

### 1. 检查现有API

运行配置检查工具：

```bash
python scripts/check_api_config.py
```

这将显示：
- 所有已注册的API路由
- API配置信息
- API文件结构
- 路由注册状态

### 2. 查看API文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## API文件结构

```
app/api/v1/
├── __init__.py              # API v1初始化文件
├── brands.py                 # 品牌管理API
├── crawl_tasks.py           # 爬虫任务API
├── analysis_tasks.py        # 分析任务API
├── reports.py               # 报告API
├── data_viewer.py           # 数据查看API
├── crawler_ui.py            # 爬虫界面API
├── mediacrawler_ui.py       # MediaCrawler界面API
├── data_analysis.py         # 数据分析API
├── data_display.py          # 数据展示API
└── dashboard.py             # 统一控制台API
```

---

## 创建新API的步骤

### 步骤1: 创建API文件

在 `app/api/v1/` 目录下创建新的Python文件，例如 `my_new_api.py`：

```python
"""
我的新API模块
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db

# 创建路由器
router = APIRouter()

# 定义请求/响应模型
class MyRequest(BaseModel):
    field1: str
    field2: Optional[int] = None

class MyResponse(BaseModel):
    id: int
    field1: str
    field2: Optional[int]
    
    class Config:
        from_attributes = True

# 定义API端点
@router.post("/my-endpoint", response_model=MyResponse)
async def create_item(
    item_data: MyRequest,
    db: Session = Depends(get_db)
):
    """创建新项目"""
    # 实现逻辑
    pass

@router.get("/my-endpoint/{item_id}", response_model=MyResponse)
async def get_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    """获取项目详情"""
    # 实现逻辑
    pass
```

### 步骤2: 在main.py中注册路由

编辑 `app/main.py`，添加导入和注册：

```python
# 在导入部分添加
from app.api.v1 import my_new_api

# 在路由注册部分添加
app.include_router(my_new_api.router, prefix=settings.API_V1_PREFIX, tags=["我的新API"])
```

### 步骤3: 测试API

1. 启动服务：
```bash
python app/main.py
# 或
uvicorn app.main:app --reload
```

2. 访问 http://localhost:8000/docs 查看新API

3. 在Swagger UI中测试API端点

---

## API开发规范

### 1. 响应格式

所有API响应应遵循统一格式：

**成功响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

**错误响应**：
```json
{
  "code": 400/404/500,
  "message": "错误信息",
  "error": "详细错误描述"
}
```

### 2. HTTP方法使用

- `GET`: 查询数据（不修改状态）
- `POST`: 创建新资源
- `PUT`: 完整更新资源
- `PATCH`: 部分更新资源
- `DELETE`: 删除资源

### 3. 状态码

- `200`: 成功
- `201`: 创建成功
- `204`: 删除成功（无内容）
- `400`: 请求参数错误
- `401`: 未授权
- `403`: 禁止访问
- `404`: 资源不存在
- `422`: 验证失败
- `500`: 服务器内部错误

### 4. 分页

对于列表API，应支持分页：

```python
@router.get("/items")
async def get_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取项目列表"""
    query = db.query(Item)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": [...],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }
```

### 5. 错误处理

使用HTTPException处理错误：

```python
from fastapi import HTTPException

@router.get("/items/{item_id}")
async def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="项目不存在")
    return item
```

### 6. 数据验证

使用Pydantic模型进行数据验证：

```python
from pydantic import BaseModel, Field, validator

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=500)
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('名称不能为空')
        return v.strip()
```

---

## 示例：创建一个新的API模块

假设我们要创建一个"通知管理"API模块。

### 1. 创建数据模型（如果需要）

在 `app/models/` 目录下创建 `notification.py`：

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### 2. 创建API文件

在 `app/api/v1/` 目录下创建 `notifications.py`：

```python
"""
通知管理API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.notification import Notification

router = APIRouter()


# 请求模型
class NotificationCreate(BaseModel):
    title: str
    content: Optional[str] = ""


class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_read: Optional[bool] = None


# 响应模型
class NotificationResponse(BaseModel):
    id: int
    title: str
    content: Optional[str]
    is_read: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


@router.post("/notifications", response_model=dict, status_code=201)
async def create_notification(
    notification_data: NotificationCreate,
    db: Session = Depends(get_db)
):
    """创建通知"""
    notification = Notification(
        title=notification_data.title,
        content=notification_data.content
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    return {
        "code": 200,
        "message": "success",
        "data": NotificationResponse(
            id=notification.id,
            title=notification.title,
            content=notification.content,
            is_read=notification.is_read,
            created_at=notification.created_at.isoformat(),
            updated_at=notification.updated_at.isoformat()
        ).dict()
    }


@router.get("/notifications", response_model=dict)
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    is_read: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """获取通知列表"""
    query = db.query(Notification)
    
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
    
    total = query.count()
    items = query.order_by(Notification.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": [
                NotificationResponse(
                    id=item.id,
                    title=item.title,
                    content=item.content,
                    is_read=item.is_read,
                    created_at=item.created_at.isoformat(),
                    updated_at=item.updated_at.isoformat()
                ).dict()
                for item in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


@router.get("/notifications/{notification_id}", response_model=dict)
async def get_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """获取通知详情"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    return {
        "code": 200,
        "message": "success",
        "data": NotificationResponse(
            id=notification.id,
            title=notification.title,
            content=notification.content,
            is_read=notification.is_read,
            created_at=notification.created_at.isoformat(),
            updated_at=notification.updated_at.isoformat()
        ).dict()
    }


@router.put("/notifications/{notification_id}", response_model=dict)
async def update_notification(
    notification_id: int,
    notification_data: NotificationUpdate,
    db: Session = Depends(get_db)
):
    """更新通知"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    if notification_data.title is not None:
        notification.title = notification_data.title
    if notification_data.content is not None:
        notification.content = notification_data.content
    if notification_data.is_read is not None:
        notification.is_read = notification_data.is_read
    
    db.commit()
    db.refresh(notification)
    
    return {
        "code": 200,
        "message": "success",
        "data": NotificationResponse(
            id=notification.id,
            title=notification.title,
            content=notification.content,
            is_read=notification.is_read,
            created_at=notification.created_at.isoformat(),
            updated_at=notification.updated_at.isoformat()
        ).dict()
    }


@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """删除通知"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    db.delete(notification)
    db.commit()
    
    from fastapi import Response
    return Response(status_code=204)
```

### 3. 在main.py中注册

编辑 `app/main.py`：

```python
# 在导入部分添加
from app.api.v1 import notifications

# 在路由注册部分添加
app.include_router(notifications.router, prefix=settings.API_V1_PREFIX, tags=["通知管理"])
```

### 4. 运行数据库迁移（如果需要）

如果创建了新的数据模型，需要创建数据库表：

```python
# 在 app/core/database.py 中导入新模型
from app.models.notification import Notification

# 运行初始化脚本
python scripts/init_database.py
```

---

## 常见问题

### Q1: 如何添加认证？

如果需要JWT认证，可以创建依赖项：

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # 验证token逻辑
    token = credentials.credentials
    # ... 验证token
    return user

# 在路由中使用
@router.get("/protected")
async def protected_route(user = Depends(get_current_user)):
    return {"user": user}
```

### Q2: 如何处理文件上传？

```python
from fastapi import UploadFile, File

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # 保存文件
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"filename": file.filename}
```

### Q3: 如何添加WebSocket支持？

```python
from fastapi import WebSocket

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
```

### Q4: 如何添加中间件？

在 `app/main.py` 中添加：

```python
@app.middleware("http")
async def custom_middleware(request, call_next):
    # 处理逻辑
    response = await call_next(request)
    return response
```

### Q5: 如何添加CORS？

已在 `app/main.py` 中配置，如需修改：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 允许的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 检查清单

创建新API后，请检查：

- [ ] API文件已创建并定义了 `router`
- [ ] 在 `main.py` 中导入并注册了路由
- [ ] 请求/响应模型已定义
- [ ] 错误处理已实现
- [ ] 响应格式符合规范
- [ ] 已添加适当的HTTP状态码
- [ ] 已添加API文档字符串
- [ ] 已在Swagger UI中测试
- [ ] 代码已通过lint检查
- [ ] 已更新API设计文档（如需要）

---

## 相关文档

- [API设计文档](api_design.md)
- [项目架构文档](../项目架构文档.md)
- [数据库设计文档](database_design.md)

---

**最后更新**: 2026-01-06


