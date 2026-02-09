"""
测试模板文件 - 复制此文件创建新的测试

使用说明:
1. 复制此文件到相应目录
2. 重命名为 test_功能名称.py
3. 根据测试类型选择合适的基类
4. 实现具体的测试方法
"""

# 对于不需要数据库的纯逻辑测试
from django.test import SimpleTestCase

class TestTemplateLogic(SimpleTestCase):
    """测试模板 - 逻辑测试类"""
    
    def setUp(self):
        """测试前准备"""
        pass
    
    def tearDown(self):
        """测试后清理"""
        pass
    
    def test_example_logic(self):
        """示例逻辑测试"""
        # Arrange (准备)
        input_data = "test"
        
        # Act (执行)
        result = len(input_data)
        
        # Assert (断言)
        self.assertEqual(result, 4)


# 对于需要数据库操作的测试
from django.test import TestCase
from apps.your_app.models import YourModel

class TestTemplateWithDatabase(TestCase):
    """测试模板 - 数据库测试类"""
    
    @classmethod
    def setUpTestData(cls):
        """测试类级别的数据准备（只执行一次）"""
        # 创建测试数据
        cls.test_object = YourModel.objects.create(
            name="Test Object",
            # 其他字段...
        )
    
    def setUp(self):
        """每个测试方法前的准备"""
        pass
    
    def tearDown(self):
        """每个测试方法后的清理"""
        pass
    
    def test_model_creation(self):
        """测试模型创建"""
        # 测试代码...
        pass
    
    def test_model_methods(self):
        """测试模型方法"""
        # 测试代码...
        pass


# 测试最佳实践提示:
"""
1. 测试方法命名: test_[动作]_[预期结果]
2. 遵循 AAA 模式: Arrange-Act-Assert
3. 保持测试独立性，避免相互依赖
4. 使用 descriptive 的测试名称
5. 每个测试只测试一个功能点
6. 合理使用 setUp 和 setUpTestData
7. 记得清理测试数据
8. 添加适当的文档字符串
"""

# 常用断言方法:
"""
self.assertEqual(a, b)          # 相等
self.assertNotEqual(a, b)       # 不相等
self.assertTrue(x)              # 为真
self.assertFalse(x)             # 为假
self.assertIsNone(x)            # 为None
self.assertIsNotNone(x)         # 不为None
self.assertIn(a, b)             # 包含
self.assertNotIn(a, b)          # 不包含
self.assertGreater(a, b)        # 大于
self.assertLess(a, b)           # 小于
self.assertRaises(Exception)    # 抛出异常
"""

# 运行测试的命令:
"""
# 运行单个测试文件
python manage.py test path.to.your.test_file

# 运行测试类
python manage.py test path.to.your.test_file.TestClassName

# 运行单个测试方法
python manage.py test path.to.your.test_file.TestClassName.test_method_name

# 详细输出
python manage.py test -v 2

# 保留测试数据库（调试时有用）
python manage.py test --keepdb
"""