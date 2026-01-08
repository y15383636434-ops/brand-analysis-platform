# LLM聚合网关配置指南

> 最后更新：2026-01-07

## 📋 概述

本项目支持通过 **LLM聚合网关**（基于 OneAPI/NewAPI）统一接入多个LLM模型，实现：
- ✅ 统一接口管理多模型（GPT-4o, Claude 3.5, Gemini等）
- ✅ 动态切换模型，无需修改代码
- ✅ 负载均衡与故障转移
- ✅ 完全兼容OpenAI SDK格式

## 🔧 配置步骤

### 1. 获取聚合网关信息

从您的LLM聚合网关管理台（例如：`https://xy.xiaoxu030.xyz:8888/console`）获取：
- **Base URL**: `https://xy.xiaoxu030.xyz:8888/v1`（注意：必须以 `/v1` 结尾）
- **API Key**: 在管理台生成的令牌（通常以 `sk-` 开头）
- **模型名称**: 您要使用的模型名称（例如：`gpt-4o-mini`, `claude-3-5-sonnet`）

### 2. 配置环境变量

创建或编辑项目根目录下的 `.env` 文件：

```bash
# LLM聚合网关配置（推荐）
LLM_API_BASE=https://xy.xiaoxu030.xyz:8888/v1
LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxx
LLM_MODEL_NAME=gpt-4o-mini
```

### 3. 或在config.py中直接配置

编辑 `config.py` 文件：

```python
class Settings(BaseSettings):
    # ... 其他配置 ...
    
    # LLM聚合网关配置（优先使用）
    LLM_API_BASE: Optional[str] = "https://xy.xiaoxu030.xyz:8888/v1"
    LLM_API_KEY: Optional[str] = "sk-xxxxxxxxxxxxxxxxxxxxxxx"
    LLM_MODEL_NAME: Optional[str] = "gpt-4o-mini"
```

### 4. 验证配置

启动服务后，查看日志输出：

```
使用LLM聚合网关: https://xy.xiaoxu030.xyz:8888/v1, 模型: gpt-4o-mini
```

## 🎯 工作原理

### 调用优先级

系统按以下优先级调用LLM服务：

1. **LLM聚合网关**（如果配置了 `LLM_API_KEY` 和 `LLM_API_BASE`）
2. OpenAI（直接调用）
3. Gemini
4. Claude
5. 本地LLM

### 故障转移

如果聚合网关调用失败，系统会自动降级到直接调用OpenAI（如果已配置）。

## 📝 配置示例

### 示例1：使用聚合网关（推荐）

```bash
# .env 文件
LLM_API_BASE=https://xy.xiaoxu030.xyz:8888/v1
LLM_API_KEY=sk-abc123def456ghi789
LLM_MODEL_NAME=gpt-4o-mini
```

### 示例2：使用聚合网关 + OpenAI备用

```bash
# .env 文件
# 优先使用聚合网关
LLM_API_BASE=https://xy.xiaoxu030.xyz:8888/v1
LLM_API_KEY=sk-abc123def456ghi789
LLM_MODEL_NAME=gpt-4o-mini

# 备用方案：直接调用OpenAI
OPENAI_API_KEY=sk-your-openai-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
```

### 示例3：仅使用直接调用（不使用聚合网关）

```bash
# .env 文件
# 不配置 LLM_API_BASE 和 LLM_API_KEY
# 直接使用OpenAI
OPENAI_API_KEY=sk-your-openai-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
```

## 🔍 常见问题

### Q1: Base URL应该使用什么格式？

**A**: 必须使用 `/v1` 结尾的地址，例如：
- ✅ 正确：`https://xy.xiaoxu030.xyz:8888/v1`
- ❌ 错误：`https://xy.xiaoxu030.xyz:8888/console`（这是管理台地址，不是API地址）

### Q2: 如何切换模型？

**A**: 修改 `LLM_MODEL_NAME` 环境变量即可，无需修改代码：

```bash
# 切换到Claude模型
LLM_MODEL_NAME=claude-3-5-sonnet

# 切换到Gemini模型
LLM_MODEL_NAME=gemini-2.0-flash-exp
```

### Q3: 如何查看当前使用的模型？

**A**: 在分析结果中会显示当前使用的模型，格式为：`Gateway-{模型名称}`

### Q4: 聚合网关调用失败怎么办？

**A**: 系统会自动降级到直接调用OpenAI（如果已配置）。您也可以检查：
1. Base URL是否正确（必须以 `/v1` 结尾）
2. API Key是否有效
3. 模型名称是否在网关中配置

### Q5: 可以同时配置多个模型吗？

**A**: 可以，但系统会按优先级使用。建议：
- 主要使用聚合网关（配置 `LLM_API_BASE`）
- 配置OpenAI作为备用（配置 `OPENAI_API_KEY`）

## 📚 相关文档

- [项目架构文档](../项目架构文档.md) - 查看整体架构
- [API设计文档](api_design.md) - 查看API接口
- [新API配置指南](新API配置指南.md) - 了解如何添加新API

## 🔗 相关链接

- **聚合网关管理台**: `https://xy.xiaoxu030.xyz:8888/console`（示例）
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

---

**提示**: 配置完成后，重启服务使配置生效。


