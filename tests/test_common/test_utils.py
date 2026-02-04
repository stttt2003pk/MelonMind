import pytest
from apps.common.utils import (
    format_response, validate_json, mask_sensitive_data,
    extract_ip_addresses, is_valid_email
)


class TestUtils:
    """测试通用工具函数"""
    
    def test_format_response_success(self):
        """测试成功响应格式化"""
        response = format_response(True, {'test': 'data'}, '操作成功')
        assert response['success'] is True
        assert response['data'] == {'test': 'data'}
        assert response['message'] == '操作成功'
    
    def test_format_response_error(self):
        """测试错误响应格式化"""
        response = format_response(False, None, '操作失败', 'ERR_001')
        assert response['success'] is False
        assert response['error_code'] == 'ERR_001'
    
    def test_validate_json_valid(self):
        """测试有效的JSON"""
        valid_json = '{"key": "value"}'
        assert validate_json(valid_json) is True
    
    def test_validate_json_invalid(self):
        """测试无效的JSON"""
        invalid_json = '{"key": "value"'
        assert validate_json(invalid_json) is False
    
    def test_mask_sensitive_data(self):
        """测试敏感数据掩码"""
        data = {
            'username': 'admin',
            'password': 'secret123',
            'token': 'abc123',
            'normal_field': 'normal_value'
        }
        
        masked = mask_sensitive_data(data)
        assert masked['password'] == '***MASKED***'
        assert masked['token'] == '***MASKED***'
        assert masked['normal_field'] == 'normal_value'
    
    def test_extract_ip_addresses(self):
        """测试IP地址提取"""
        text = "服务器IP是192.168.1.1，网关是192.168.1.254"
        ips = extract_ip_addresses(text)
        assert '192.168.1.1' in ips
        assert '192.168.1.254' in ips
    
    def test_is_valid_email(self):
        """测试邮箱验证"""
        assert is_valid_email('test@example.com') is True
        assert is_valid_email('invalid-email') is False
        assert is_valid_email('test@') is False