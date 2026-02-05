# MelonMind 调试助手

## 🐛 常见错误诊断和解决

### 1. 依赖相关问题

#### Poetry 安装失败
```bash
# 错误症状: poetry install 失败
# 解决方案:
poetry cache clear pypi --all
poetry lock --no-update
poetry install

# 如果仍有问题:
rm poetry.lock
poetry install
```

#### 版本冲突
```bash
# 查看冲突详情
poetry show --tree

# 更新特定包
poetry update package-name

# 强制解析依赖
poetry lock --no-update
```

### 2. 数据库问题

#### 迁移相关错误
```bash
# 重置迁移文件
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# 重新创建迁移
python manage.py makemigrations
python manage.py migrate

# 如果需要强制迁移
python manage.py migrate --fake-initial
```

#### 连接超时
```bash
# 检查数据库服务状态
pg_isready -h localhost -p 5432

# 检查连接配置
python manage.py dbshell
\conninfo
```

### 3. Milvus 相关问题

#### 连接失败诊断
```python
# 在 Django shell 中测试连接
python manage.py shell

from apps.mulvesdb.connectors import MilvusConnector
connector = MilvusConnector()
print("连接状态:", connector.check_connection())
print("集合列表:", connector.list_collections())
```

#### Docker 容器问题
```bash
# 查看容器状态
docker-compose -f apps/mulvesdb/dev_utils/docker-compose.yml ps

# 查看日志
docker-compose -f apps/mulvesdb/dev_utils/docker-compose.yml logs milvus-standalone

# 重启服务
docker-compose -f apps/mulvesdb/dev_utils/docker-compose.yml restart
```

### 4. 测试相关问题

#### Mock 服务配置
```bash
# 确保使用正确的环境变量
export USE_MOCK_EMBEDDING=true
export MOCK_EMBEDDING_DIMENSION=1536

# 运行测试时显示详细信息
python -m pytest tests/ -v -s --tb=short
```

#### 测试数据库隔离
```python
# 在测试中手动清理数据
from django.test import TestCase

class MyTestCase(TestCase):
    def setUp(self):
        # 清理测试数据
        MyModel.objects.all().delete()
    
    def tearDown(self):
        # 测试后清理
        pass
```

## 🔍 调试技巧

### 1. 日志调试
```python
# 在代码中添加详细日志
import logging
logger = logging.getLogger(__name__)

logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
```

### 2. Django 调试工具
```python
# 在视图中调试请求
from django.http import JsonResponse

def debug_view(request):
    return JsonResponse({
        'GET_params': dict(request.GET),
        'POST_params': dict(request.POST),
        'headers': dict(request.headers),
        'user': str(request.user),
    })
```

### 3. 数据库查询调试
```python
# 查看生成的 SQL
from django.db import connection

qs = MyModel.objects.filter(name='test')
print(qs.query)  # 显示 SQL 查询

# 查看最近的查询
print(connection.queries)
```

## 📊 性能分析

### 1. 查询性能
```python
# 使用 Django Debug Toolbar 分析查询
# 在 settings.py 中启用:
DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.timer.TimerPanel',
]

# 或者手动分析:
from django.db import reset_queries, connection
reset_queries()
# 执行你的查询
print(len(connection.queries))  # 查询数量
```

### 2. 内存使用
```python
import tracemalloc

tracemalloc.start()
# 执行可能内存泄漏的代码
current, peak = tracemalloc.get_traced_memory()
print(f"当前内存使用: {current / 1024 / 1024:.1f} MB")
print(f"峰值内存使用: {peak / 1024 / 1024:.1f} MB")
tracemalloc.stop()
```

## 🛠️ 开发工具推荐

### 1. IDE 配置
```python
# PyCharm 配置建议:
# - Interpreter: 选择 Poetry 创建的虚拟环境
# - Django settings: config.settings
# - Environment variables: 从 .env 文件加载
```

### 2. 有用的扩展
```bash
# 安装开发辅助工具
poetry add --group dev django-debug-toolbar
poetry add --group dev django-extensions
poetry add --group dev ipython

# 使用 django-extensions 的 shell_plus
python manage.py shell_plus --print-sql
```

## 📋 检查清单

### 部署前检查
- [ ] 所有测试通过
- [ ] 代码符合 PEP8 标准
- [ ] 安全检查通过 (`python manage.py check --deploy`)
- [ ] 数据库迁移已应用
- [ ] 静态文件已收集
- [ ] 环境变量已正确设置

### 开发环境检查
- [ ] Poetry 环境正常
- [ ] 数据库连接正常
- [ ] Milvus 服务运行中
- [ ] 必要的环境变量已设置
- [ ] 测试数据已准备

这个调试助手文档包含了最常见的问题和解决方案，希望能帮助您快速定位和解决问题！