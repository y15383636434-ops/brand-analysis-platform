# 🚀 快速测试API服务

## 📋 测试前准备

### 1. 启动服务

**方式1：使用批处理文件（推荐）**
```bash
启动FastAPI.bat
```

**方式2：使用Python命令**
```bash
python app/main.py
```

**方式3：使用uvicorn**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

启动成功后，您会看到：
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 2. 运行测试脚本

```bash
python scripts/test_api_service.py
```

这会自动测试：
- ✅ 健康检查
- ✅ API基础路径
- ✅ 品牌管理API
- ✅ 创建品牌API
- ✅ 爬虫任务API
- ✅ 分析API
- ✅ Dashboard

## 🌐 使用浏览器测试

### 1. Swagger UI（推荐）

访问：http://localhost:8000/docs

**功能：**
- 查看所有API文档
- 直接在浏览器中测试API
- 查看请求/响应格式
- 无需编写代码

**使用步骤：**
1. 打开 http://localhost:8000/docs
2. 找到要测试的API（例如：`POST /api/v1/brands`）
3. 点击 "Try it out"
4. 填写参数
5. 点击 "Execute"
6. 查看响应结果

### 2. ReDoc

访问：http://localhost:8000/redoc

**功能：**
- 更美观的API文档界面
- 适合阅读文档
- 不支持直接测试

### 3. Dashboard（统一控制台）

访问：http://localhost:8000/api/v1/dashboard

**功能：**
- 品牌管理界面
- 数据采集界面
- 数据分析界面
- 报告查看界面

## 🔧 使用命令行测试

### 1. 健康检查

```bash
curl http://localhost:8000/health
```

或使用PowerShell：
```powershell
Invoke-WebRequest -Uri http://localhost:8000/health
```

### 2. 获取品牌列表

```bash
curl http://localhost:8000/api/v1/brands
```

### 3. 创建品牌

```bash
curl -X POST http://localhost:8000/api/v1/brands ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"测试品牌\",\"description\":\"测试\",\"keywords\":[\"测试\"],\"platforms\":[\"xhs\"]}"
```

### 4. 获取品牌详情

```bash
curl http://localhost:8000/api/v1/brands/1
```

## 📊 测试清单

### ✅ 基础功能

- [ ] 服务启动成功
- [ ] 健康检查正常
- [ ] Swagger UI可以访问
- [ ] Dashboard可以访问

### ✅ 品牌管理

- [ ] 创建品牌成功
- [ ] 获取品牌列表成功
- [ ] 获取品牌详情成功
- [ ] 更新品牌成功
- [ ] 删除品牌成功

### ✅ 数据采集

- [ ] 启动爬虫任务成功
- [ ] 查看任务状态成功
- [ ] 任务可以正常执行

### ✅ AI分析

- [ ] 启动分析任务成功
- [ ] 查看分析结果成功
- [ ] LLM分析功能正常

## 🐛 常见问题

### Q1: 连接被拒绝

**错误：** `ConnectionError` 或 `无法连接到服务`

**解决：**
1. 确认服务已启动
2. 检查端口8000是否被占用
3. 查看服务日志：`type logs\app.log`

### Q2: 404错误

**错误：** `404 Not Found`

**解决：**
1. 检查API路径是否正确（应该是 `/api/v1/...`）
2. 查看Swagger UI确认正确的路径

### Q3: 500错误

**错误：** `500 Internal Server Error`

**解决：**
1. 查看服务日志：`type logs\app.log`
2. 检查数据库连接
3. 检查LLM API配置

### Q4: 422错误

**错误：** `422 Validation Error`

**解决：**
1. 检查请求参数格式
2. 查看Swagger UI中的参数说明
3. 确保必填字段都已填写

## 📝 测试示例

### 示例1：创建品牌并分析

```bash
# 1. 创建品牌
curl -X POST http://localhost:8000/api/v1/brands \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试品牌",
    "description": "测试描述",
    "keywords": ["测试"],
    "platforms": ["xhs"]
  }'

# 2. 获取品牌ID（假设返回的ID是1）
# 3. 启动分析
curl -X POST http://localhost:8000/api/v1/brands/1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "full",
    "include_sentiment": true,
    "include_topics": true,
    "include_keywords": true,
    "include_insights": true
  }'

# 4. 查看分析结果
curl http://localhost:8000/api/v1/brands/1/analysis
```

## 🎯 推荐测试流程

1. **运行自动化测试**
   ```bash
   python scripts/test_api_service.py
   ```

2. **使用Swagger UI测试**
   - 访问 http://localhost:8000/docs
   - 测试各个API端点

3. **使用Dashboard测试**
   - 访问 http://localhost:8000/api/v1/dashboard
   - 测试完整业务流程

4. **查看日志**
   - 查看 `logs/app.log` 了解详细运行情况

## 📚 相关文档

- [完整测试指南](完整测试指南.md)
- [API设计文档](docs/api_design.md)
- [项目架构文档](项目架构文档.md)

---

**提示**：建议先运行自动化测试脚本，然后使用Swagger UI进行详细测试。


