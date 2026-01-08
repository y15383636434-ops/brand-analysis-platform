# PyCharm运行配置指南

## ⚠️ 问题说明

`scripts/test_llm_api.py` 等文件是**普通Python脚本**，不是pytest测试文件。PyCharm自动识别为pytest测试会导致错误。

## ✅ 解决方案

### 方案1：在PyCharm中正确运行（推荐）

#### 步骤1：创建Python运行配置

1. 打开 **Run** → **Edit Configurations...**（或按 `Alt+Shift+F10` → `0`）

2. 点击左上角的 **+** 号，选择 **Python**

3. 配置如下：
   - **Name**: `test_llm_api`
   - **Script path**: 点击文件夹图标，选择 `C:\Users\Yu\cursorProjects\githup\scripts\test_llm_api.py`
   - **Working directory**: `C:\Users\Yu\cursorProjects\githup`
   - **Python interpreter**: 选择您的Python 3.13解释器

4. 点击 **OK** 保存

#### 步骤2：运行配置

1. 在PyCharm顶部工具栏选择刚创建的配置 `test_llm_api`
2. 点击绿色运行按钮（或按 `Shift+F10`）

#### 步骤3：删除pytest配置（如果有）

1. 在 **Run** → **Edit Configurations...** 中
2. 找到所有pytest相关的配置（名称包含 `pytest` 或 `test_llm_api`）
3. 选中并点击 **-** 号删除

### 方案2：直接运行（最简单）

1. 在PyCharm中打开 `scripts/test_llm_api.py`
2. 右键点击文件内容区域
3. 选择 **Run 'test_llm_api'**（不是 "Run pytest"）
4. 或者点击文件右上角的绿色运行按钮

### 方案3：禁用pytest自动检测

1. 打开 **File** → **Settings**（或按 `Ctrl+Alt+S`）
2. 导航到 **Tools** → **Python Integrated Tools**
3. 在 **Testing** 部分：
   - **Default test runner**: 选择 **Unittests** 或 **None**
   - 取消勾选 **Auto-detection of test frameworks**
4. 点击 **OK**

### 方案4：使用命令行运行

在PyCharm的Terminal中运行：

```bash
python scripts/test_llm_api.py
```

## 🔧 为每个测试脚本创建运行配置

### test_llm_api.py

- **Name**: `test_llm_api`
- **Script path**: `$ProjectFileDir$/scripts/test_llm_api.py`
- **Working directory**: `$ProjectFileDir$`

### test_api_quick.py

- **Name**: `test_api_quick`
- **Script path**: `$ProjectFileDir$/scripts/test_api_quick.py`
- **Working directory**: `$ProjectFileDir$`

### test_api_service.py

- **Name**: `test_api_service`
- **Script path**: `$ProjectFileDir$/scripts/test_api_service.py`
- **Working directory**: `$ProjectFileDir$`

### list_available_models.py

- **Name**: `list_available_models`
- **Script path**: `$ProjectFileDir$/scripts/list_available_models.py`
- **Working directory**: `$ProjectFileDir$`

## 📝 快速操作步骤

### 方法A：使用右键菜单

1. 在项目树中找到 `scripts/test_llm_api.py`
2. 右键点击文件
3. 选择 **Run 'test_llm_api'**（如果看到这个选项）
4. 如果没有，选择 **Run** → **Run 'test_llm_api'**

### 方法B：使用代码编辑器

1. 打开 `scripts/test_llm_api.py` 文件
2. 在代码编辑器中右键点击
3. 选择 **Run 'test_llm_api'**
4. 或者点击文件右上角的绿色运行按钮

### 方法C：使用快捷键

1. 打开 `scripts/test_llm_api.py` 文件
2. 按 `Ctrl+Shift+F10`（运行当前文件）
3. 如果提示选择运行器，选择 **Python**，不是 **pytest**

## 🎯 验证配置

运行后应该看到类似输出：
```
================================================================================
品牌分析系统 - API配置测试
================================================================================
...
✅ API调用成功！
...
```

**不应该**看到：
```
============================= test session starts =============================
collecting ...
Skipped: 这不是pytest测试文件...
```

## 💡 提示

- 如果PyCharm仍然尝试用pytest运行，检查是否有pytest运行配置
- 删除所有pytest相关的运行配置
- 使用 `Ctrl+Shift+F10` 快速运行当前文件
- 在Terminal中使用命令行运行是最可靠的方法

## 📚 相关文档

- [如何运行测试脚本](如何运行测试脚本.md)
- [完整测试指南](完整测试指南.md)


