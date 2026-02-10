"""
调试示例测试文件
用于演示 VSCode 调试功能
"""

import pytest
from django.test import TestCase
from unittest.mock import patch, MagicMock

class TestDebugExample(TestCase):
    """调试示例测试类"""
    
    def setUp(self):
        """测试前置设置"""
        print("Setting up test...")
        self.test_data = {"name": "test", "value": 42}
    
    def tearDown(self):
        """测试后置清理"""
        print("Tearing down test...")
    
    def test_basic_assertion(self):
        """基本断言测试"""
        assert self.test_data["value"] == 42
        assert self.test_data["name"] == "test"
    
    @patch('builtins.print')
    def test_mock_example(self, mock_print):
        """Mock 示例测试"""
        # 模拟打印函数
        print("Hello, World!")
        mock_print.assert_called_once_with("Hello, World!")
    
    def test_exception_handling(self):
        """异常处理测试"""
        with pytest.raises(KeyError):
            _ = self.test_data["nonexistent_key"]
    
    @pytest.mark.skip(reason="示例跳过测试")
    def test_skipped(self):
        """跳过的测试"""
        assert False, "这个测试应该被跳过"
    
    @pytest.mark.xfail(reason="示例预期失败测试")
    def test_expected_failure(self):
        """预期失败的测试"""
        assert 1 == 2, "这应该失败"

def test_fixture_example():
    """Fixture 示例测试"""
    def sample_fixture():
        return {"data": "fixture_data"}
    
    fixture_data = sample_fixture()
    assert fixture_data["data"] == "fixture_data"

if __name__ == "__main__":
    # 可以直接运行这个文件进行调试
    pytest.main([__file__, "-v"])