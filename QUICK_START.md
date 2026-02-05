# MelonMind 快速开始指南

## 🚀 一分钟快速启动

### 1. 环境准备
```bash
# 克隆项目后进入目录
cd MelonMind

# 激活 Poetry 环境
poetry env info --path
source /path/to/.venv/bin/activate
# 或者直接使用: poetry shell (如果支持)
```

### 2. 安装依赖
```bash
# 如果遇到依赖冲突，先更新锁文件
poetry lock
poetry install
```

### 3. 数据库初始化
```bash
# 运行迁移
poetry run python manage.py migrate

# 创建管理员账户
poetry run python manage.py createsuperuser
```

### 4. 启动服务
```bash
# 启动开发服务器
poetry run python manage.py runserver

# 访问 http://localhost:8000/
```

## 🔧 常用快捷操作

### 测试运行
```bash
# 快速测试
poetry run python -m pytest tests/test_homepage/

# 详细测试输出
poetry run python -m pytest -v tests/

# 测试特定功能
poetry run python -m pytest tests/test_pdf_loader/test_core_functionality.py
```

### 开发调试
```bash
# 检查项目状态
poetry run python manage.py check

# 查看路由
poetry run python manage.py show_urls

# 进入 Django shell
poetry run python manage.py shell
```

## 📁 项目核心模块快速导航

| 功能 | 路径 | 说明 |
|------|------|------|
| 主页 | `/` | 欢迎页面和API入口 |
| PDF加载 | `/api/pdfloader/` | 文档上传和处理 |
| 知识库 | `/api/knowledge-base/` | 向量检索和查询 |
| Milvus集成 | `apps/mulvesdb/` | 向量数据库连接 |

## ⚡ 常见问题快速解决

### Poetry 环境问题
```bash
# 重新创建环境
poetry env remove python
poetry install
```

### 数据库连接失败
```bash
# 检查 PostgreSQL 是否运行
brew services list | grep postgresql

# 启动 PostgreSQL
brew services start postgresql
```

### Milvus 连接问题
```bash
# 启动本地 Milvus
cd apps/mulvesdb/dev_utils/
docker-compose up -d milvus-etcd milvus-minio milvus-standalone
```

### 测试环境变量
```bash
# 设置测试环境变量
export USE_MOCK_EMBEDDING=true
export DJANGO_SETTINGS_MODULE=config.settings
```

## 🎯 开发工作流

### 1. 日常开发循环
```bash
# 1. 激活环境
poetry shell

# 2. 运行开发服务器
python manage.py runserver

# 3. 另一个终端运行测试
python -m pytest -x  # 遇到错误立即停止
```

### 2. 添加新功能
```bash
# 1. 创建新应用
python manage.py startapp new_feature

# 2. 添加到 INSTALLED_APPS
# 3. 创建模型和视图
# 4. 编写测试
# 5. 运行测试验证
python -m pytest tests/test_new_feature/
```

### 3. 部署前检查
```bash
# 代码质量检查
python manage.py check --deploy

# 安全检查
python manage.py check --tag security

# 运行完整测试套件
python -m pytest --cov=apps
```

## 📞 获取帮助

- 查看完整文档: `docs/index.md`
- 查看测试说明: `tests/README.md`
- 查看详细提示: `PROMPTS.md`

这个快速开始指南旨在让您在最短时间内让项目运行起来并开始开发！