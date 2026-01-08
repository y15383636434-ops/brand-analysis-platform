# GitHub 推送指南

## 📋 前提条件

1. 已安装 Git
2. 已创建 GitHub 账号
3. 已在 GitHub 上创建仓库（如果还没有，请先创建）

## 🚀 推送步骤

### 方式一：已有 GitHub 仓库

如果你已经在 GitHub 上创建了仓库，执行以下命令：

```bash
# 1. 添加远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/你的用户名/你的仓库名.git

# 2. 推送到 GitHub
git push -u origin master
```

### 方式二：创建新仓库后推送

#### 步骤1：在 GitHub 上创建新仓库

1. 登录 GitHub
2. 点击右上角的 "+" 号，选择 "New repository"
3. 填写仓库信息：
   - Repository name: `brand-analysis-platform`（或你喜欢的名字）
   - Description: `品牌分析系统 - 多平台数据采集、AI分析和报告生成平台`
   - 选择 Public 或 Private
   - **不要**勾选 "Initialize this repository with a README"（因为本地已有代码）
4. 点击 "Create repository"

#### 步骤2：推送代码

复制 GitHub 提供的仓库地址，然后执行：

```bash
# 添加远程仓库
git remote add origin https://github.com/你的用户名/你的仓库名.git

# 推送到 GitHub
git push -u origin master
```

### 方式三：使用 SSH（推荐，更安全）

如果你配置了 SSH 密钥：

```bash
# 添加 SSH 远程仓库
git remote add origin git@github.com:你的用户名/你的仓库名.git

# 推送到 GitHub
git push -u origin master
```

## 🔐 身份验证

推送时可能需要身份验证：

### 使用 Personal Access Token（推荐）

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. 点击 "Generate new token"
3. 选择权限：至少勾选 `repo` 权限
4. 生成后复制 token
5. 推送时使用 token 作为密码

### 使用 GitHub CLI

```bash
# 安装 GitHub CLI（如果还没有）
# Windows: winget install GitHub.cli

# 登录
gh auth login

# 推送
git push -u origin master
```

## 📝 常用命令

```bash
# 查看远程仓库
git remote -v

# 修改远程仓库地址
git remote set-url origin https://github.com/你的用户名/你的仓库名.git

# 推送代码
git push origin master

# 拉取代码
git pull origin master

# 查看提交历史
git log --oneline
```

## ⚠️ 注意事项

1. **MediaCrawler 子模块**：
   - 当前 MediaCrawler 作为子模块存在
   - 如果需要包含 MediaCrawler 的代码，需要单独处理
   - 或者将其从子模块中移除，直接提交代码

2. **敏感信息**：
   - 确保 `.gitignore` 已正确配置
   - 不要提交 `.env` 文件（包含数据库密码、API密钥等）
   - 不要提交日志文件和数据文件

3. **大文件**：
   - GitHub 对单个文件大小有限制（100MB）
   - 如果 MediaCrawler/python_env 目录很大，建议添加到 .gitignore

## 🛠️ 如果推送失败

### 错误1：远程仓库已存在内容

```bash
# 先拉取远程内容
git pull origin master --allow-unrelated-histories

# 解决冲突后推送
git push -u origin master
```

### 错误2：认证失败

- 检查用户名和密码（token）是否正确
- 使用 Personal Access Token 而不是 GitHub 密码
- 或者配置 SSH 密钥

### 错误3：分支名称问题

GitHub 默认分支可能是 `main` 而不是 `master`：

```bash
# 重命名本地分支
git branch -M main

# 推送到 main 分支
git push -u origin main
```

## 📚 更多帮助

- GitHub 官方文档：https://docs.github.com/
- Git 官方文档：https://git-scm.com/doc


