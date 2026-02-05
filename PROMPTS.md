# MelonMind 项目 Prompt 模板库

## 项目基本信息

- **项目名称**: MelonMind
- **项目类型**: Django REST Framework + Milvus 向量数据库
- **依赖管理**: Poetry
- **主要技术栈**: Python 3.11+, Django 4.2+, Milvus, OpenAI API

## 环境配置相关

### Poetry 环境激活
```bash
# Poetry 2.0+ 版本激活方式
poetry env info --path  # 获取虚拟环境路径
source /path/to/.venv/bin/activate  # 激活环境

# 或者直接运行命令
poetry run python manage.py runserver
```

### 环境变量设置
```bash
# 数据库配置
export DATABASE_URL="postgresql://user:password@localhost:5432/melonmind"

# Milvus 配置
export MILVUS_HOST="localhost"
export MILVUS_PORT="19530"

# OpenAI API 配置
export OPENAI_API_KEY="your-api-key-here"

# 测试相关
export USE_MOCK_EMBEDDING="true"  # 使用模拟embedding服务
export DJANGO_SETTINGS_MODULE="config.settings"
```

## 常用开发命令

### 项目启动
```bash
# 启动开发服务器
poetry run python manage.py runserver

# 启动时指定端口
poetry run python manage.py runserver 8080

# 数据库迁移
poetry run python manage.py makemigrations
poetry run python manage.py migrate

# 创建超级用户
poetry run python manage.py createsuperuser
```

### 测试执行
```bash
# 运行所有测试
poetry run python -m pytest

# 运行特定模块测试
poetry run python -m pytest tests/test_pdf_loader/

# 运行带详细输出的测试
poetry run python -m pytest -v

# 运行测试并生成覆盖率报告
poetry run python -m pytest --cov=apps --cov-report=html
```

## 项目结构说明

```
MelonMind/
├── apps/                    # Django 应用目录
│   ├── agents/             # 智能代理应用
│   ├── common/             # 公共组件
│   ├── homepage/           # 主页应用
│   ├── knowledge_base/     # 知识库应用
│   ├── mulvesdb/          # Milvus数据库集成
│   └── pdfloader/         # PDF加载器
├── config/                 # Django 配置
├── tests/                  # 测试目录
├── scripts/               # 脚本工具
└── manage.py              # Django 管理脚本
```

## 常见问题解决模板

### 依赖安装问题
```bash
# 当 pyproject.toml 与 poetry.lock 不一致时
poetry lock
poetry install

# 清理缓存重新安装
poetry cache clear pypi --all
poetry install
```

### 数据库连接问题
```bash
# 检查数据库连接
poetry run python manage.py dbshell

# 重置数据库
poetry run python manage.py flush
poetry run python manage.py migrate --run-syncdb
```

### Milvus 连接问题
```bash
# 启动本地 Milvus (使用docker-compose)
cd apps/mulvesdb/dev_utils/
docker-compose up -d

# 检查 Milvus 连接状态
poetry run python -c "from apps.mulvesdb.connectors import MilvusConnector; print(MilvusConnector().check_connection())"
```

## API 测试模板

### 使用 curl 测试 API
```bash
# 测试主页
curl http://localhost:8000/

# 测试 PDF 上传
curl -X POST http://localhost:8000/api/pdfloader/upload/ \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/document.pdf"

# 测试知识库查询
curl -X POST http://localhost:8000/api/knowledge-base/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "你的查询内容", "top_k": 5}'
```

## 调试技巧

### Django Debug Toolbar
```python
# 在 settings.py 中启用
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

### 日志配置
```python
# 在 settings.py 中添加详细日志
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

## 性能优化建议

### 数据库查询优化
```python
# 使用 select_related 和 prefetch_related
queryset = MyModel.objects.select_related('foreign_key').prefetch_related('many_to_many')

# 使用 bulk_create 批量创建
MyModel.objects.bulk_create([obj1, obj2, obj3])
```

### 缓存配置
```python
# 在 settings.py 中配置 Redis 缓存
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

这个模板库包含了项目开发中最常用的命令、配置和解决方案，可以帮助快速定位和解决问题。