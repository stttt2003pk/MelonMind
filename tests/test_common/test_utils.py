import pytest
from apps.common.utils import (
    format_response, validate_json, mask_sensitive_data,
    extract_ip_addresses, is_valid_email
)


class TestUtils:
    """Test common utility functions"""
    
    def test_format_response_success(self):
        """Test successful response formatting"""
        response = format_response(True, {'test': 'data'}, 'Operation successful')
        assert response['success'] is True
        assert response['data'] == {'test': 'data'}
        assert response['message'] == 'Operation successful'
    
    def test_format_response_error(self):
        """Test error response formatting"""
        response = format_response(False, None, 'Operation failed', 'ERR_001')
        assert response['success'] is False
        assert response['error_code'] == 'ERR_001'
    
    def test_validate_json_valid(self):
        """Test valid JSON"""
        valid_json = '{"key": "value"}'
        assert validate_json(valid_json) is True
    
    def test_validate_json_invalid(self):
        """Test invalid JSON"""
        invalid_json = '{"key": "value"'
        assert validate_json(invalid_json) is False
    
    def test_mask_sensitive_data(self):
        """Test sensitive data masking"""
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
        """Test IP address extraction"""
        text = "Server IP is 192.168.1.1, gateway is 192.168.1.254"
        ips = extract_ip_addresses(text)
        assert '192.168.1.1' in ips
        assert '192.168.1.254' in ips
    
    def test_is_valid_email(self):
        """Test email validation"""
        assert is_valid_email('test@example.com') is True
        assert is_valid_email('invalid-email') is False
        assert is_valid_email('test@') is False