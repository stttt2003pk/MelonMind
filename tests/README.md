# 测试指南

## 📋 测试类型说明

本项目包含多种类型的测试，每种测试适用于不同的场景：

### 1. 单元测试 (Unit Tests)
- **位置**: `tests/test_*/test_*.py`
- **基类**: `unittest.TestCase` 或 `django.test.SimpleTestCase`
- **特点**: 不需要数据库，使用mock模拟外部依赖
- **适用场景**: 纯函数测试、工具函数验证、业务逻辑测试

### 2. 数据库测试 (Database Tests)
- **位置**: `tests/test_*/test_*_with_db.py`
- **基类**: `django.test.TestCase`
- **特点**: 需要真实数据库操作
- **适用场景**: 模型操作、数据库查询、事务测试

### 3. 集成测试 (Integration Tests)
- **位置**: `tests/test_*/integration/`
- **基类**: `django.test.TestCase` 或自定义
- **特点**: 测试多个组件协同工作
- **适用场景**: API端点测试、完整业务流程测试

## 🛠️ 测试环境配置

### PostgreSQL测试环境
项目已配置自定义测试运行器解决PostgreSQL兼容性问题：

```python
# config/settings.py
TEST_RUNNER = 'tests.custom_test_runner.CustomTestRunner'
```

**优势**:
- ✅ 完全兼容PostgreSQL
- ✅ 无需特殊配置即可运行
- ✅ 自动处理数据库创建和清理

### 临时SQLite环境
如需临时使用SQLite进行快速测试：

```bash
USE_SQLITE=true python manage.py test your_test_module
```

## 🎯 测试编写最佳实践

### 选择合适的测试基类

```python
# 纯逻辑测试 - 使用SimpleTestCase
from django.test import SimpleTestCase

class TestUtils(SimpleTestCase):
    def test_calculation(self):
        result = some_function(1, 2)
        self.assertEqual(result, 3)

# 数据库操作测试 - 使用TestCase
from django.test import TestCase
from myapp.models import MyModel

class TestModels(TestCase):
    def test_model_creation(self):
        obj = MyModel.objects.create(name="test")
        self.assertEqual(obj.name, "test")
```

### 测试命名规范

```
test_[动作]_[对象]_[条件].py

例如:
- test_calculate_hash_basic.py
- test_filter_duplicates_with_existing_data.py
- test_api_endpoint_returns_correct_response.py
```

### 测试数据管理

```python
class TestWithFixtures(TestCase):
    def setUp(self):
        """每个测试方法执行前的准备工作"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
    
    def tearDown(self):
        """每个测试方法执行后的清理工作"""
        # 通常不需要手动清理，TestCase会自动处理
        pass
```

## ▶️ 运行测试

### 基本命令

```bash
# 运行所有测试
python manage.py test

# 运行特定应用的测试
python manage.py test tests.test_mulvesdb

# 运行特定测试文件
python manage.py test tests.test_mulvesdb.test_chunk_deduplication

# 运行特定测试类
python manage.py test tests.test_mulvesdb.test_chunk_deduplication.TestChunkHashCalculation

# 运行特定测试方法
python manage.py test tests.test_mulvesdb.test_chunk_deduplication.TestChunkHashCalculation.test_calculate_chunk_hash_basic
```

### 详细输出

```bash
# 详细输出（级别1-3）
python manage.py test -v 2

# 失败时保留数据库
python manage.py test --keepdb

# 并行运行测试
python manage.py test --parallel
```

## 🔍 调试技巧

### 查看测试数据库内容

```bash
# 在测试过程中暂停并检查数据库
python manage.py shell --settings=config.settings_test

# 或者在测试代码中添加
import pdb; pdb.set_trace()
```

### 测试覆盖率

```bash
# 安装coverage工具
pip install coverage

# 运行带覆盖率的测试
coverage run --source='.' manage.py test

# 生成覆盖率报告
coverage report
coverage html  # 生成HTML报告
```

## ⚠️ 常见问题

### 1. PostgreSQL测试数据库创建失败

**问题**: `ProgrammingError: relation "auth_user" does not exist`

**解决方案**: 已通过自定义测试运行器解决，请确保配置了正确的TEST_RUNNER。

### 2. 测试数据污染

**问题**: 测试之间相互影响

**解决方案**: 
- 使用`TestCase`而不是`TransactionTestCase`
- 确保`setUp`和`tearDown`正确实现
- 避免在测试间共享状态

### 3. 测试速度慢

**解决方案**:
- 使用`SimpleTestCase`进行不需要数据库的测试
- 合理使用`setUpTestData`类方法
- 考虑使用factory-boy等测试数据工厂

## 📚 相关文档

- [Django官方测试文档](https://docs.djangoproject.com/en/5.2/topics/testing/)
- [PostgreSQL测试问题详细说明](../docs/DJANGO_POSTGRESQL_TEST_ISSUE.md)
- [项目特定测试配置](../config/settings.py)

## 🤝 贡献指南

编写新测试时请遵循：
1. 选择合适的测试类型和基类
2. 遵循命名规范
3. 保持测试的独立性和可重复性
4. 添加必要的文档注释
5. 确保测试覆盖率