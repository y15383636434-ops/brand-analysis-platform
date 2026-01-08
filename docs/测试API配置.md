# 测试API配置指南

## 🚀 快速测试

### 方法1：快速测试（推荐）

```bash
python scripts/test_api_quick.py
```

这会快速测试您的LLM API配置是否正常工作。

### 方法2：完整测试（包括AI服务）

```bash
python scripts/test_llm_api.py
```

这会进行完整的测试，包括：
- LLM API配置测试
- 情感分析功能测试
- 关键词提取功能测试
- LLM深度分析功能测试

### 方法3：查找可用模型

```bash
python scripts/list_available_models.py
```

这会：
- 从API获取可用模型列表
- 测试常见模型名称
- 推荐可用的模型

## 📋 测试步骤

### 步骤1：检查配置

首先检查您的配置是否正确：

```bash
python scripts/check_llm_config.py
```

应该看到：
```
✅ LLM聚合网关已配置！
```

### 步骤2：运行API测试

```bash
python scripts/test_api_quick.py
```

如果测试成功，会显示：
```
✅ API测试成功！
响应: [API返回的内容]
```

### 步骤3：启动服务测试

如果API测试通过，启动服务进行完整测试：

```bash
python app/main.py
```

然后访问：
- Swagger UI: http://localhost:8000/docs
- 测试品牌分析API

## 🔍 常见问题

### Q1: 测试失败，错误522

**原因**：网关超时或服务不可用

**解决方法**：
1. 检查聚合网关管理台是否正常运行
2. 检查网络连接
3. 尝试使用其他模型

### Q2: 测试失败，错误401

**原因**：API Key无效

**解决方法**：
1. 检查API Key是否正确
2. 在聚合网关管理台重新生成API Key
3. 更新配置：`python scripts/update_llm_config.py`

### Q3: 测试失败，错误404

**原因**：模型名称不存在

**解决方法**：
1. 检查模型名称是否正确
2. 在聚合网关管理台查看可用模型列表
3. 更新模型名称配置

### Q4: SSL证书错误

**原因**：HTTPS证书验证失败

**解决方法**：
- 如果使用自签名证书，可能需要配置SSL验证
- 或者联系网关管理员检查证书配置

## 📊 测试结果说明

### ✅ 测试通过

如果看到 `✅ API测试成功！`，说明：
- 配置正确
- API可以正常调用
- 可以开始使用服务

### ❌ 测试失败

如果测试失败，请：
1. 查看错误信息
2. 运行完整测试：`python scripts/test_llm_api.py`
3. 查找可用模型：`python scripts/list_available_models.py`
4. 检查配置：`python scripts/check_llm_config.py`
5. 根据错误信息修复问题

## 🔗 相关命令

```bash
# 检查配置
python scripts/check_llm_config.py

# 快速测试
python scripts/test_api_quick.py

# 完整测试（包括AI服务）
python scripts/test_llm_api.py

# 查找可用模型
python scripts/list_available_models.py

# 检查API配置
python scripts/check_api_config.py
```

## 📝 下一步

测试通过后：
1. 启动服务：`python app/main.py`
2. 访问 Swagger UI：http://localhost:8000/docs
3. 测试品牌分析功能
4. 查看分析结果

---

**提示**：如果测试失败，请查看错误信息并根据提示进行修复。

