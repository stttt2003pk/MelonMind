import pytest
from django.test import TestCase
from apps.agents.flows.base_flow import NetworkOperationsFlow


class TestNetworkOperationsFlow(TestCase):
    """测试网络运维流程"""
    
    def setUp(self):
        self.flow = NetworkOperationsFlow()
    
    def test_validate_input_valid(self):
        """测试输入验证 - 有效输入"""
        input_data = {
            'operation_type': 'health_check',
            'target_device': {'ip': '192.168.1.1'}
        }
        self.assertTrue(self.flow.validate_input(input_data))
    
    def test_execute_health_check(self):
        """测试健康检查执行"""
        input_data = {
            'operation_type': 'health_check',
            'target_device': {'ip': '192.168.1.1'}
        }
        
        result = self.flow.execute(input_data)
        self.assertEqual(result['status'], 'completed')
        self.assertIn('result', result)
    
    def test_execute_backup_configuration(self):
        """测试配置备份执行"""
        input_data = {
            'operation_type': 'configuration_backup',
            'target_device': {'ip': '192.168.1.1'}
        }
        
        result = self.flow.execute(input_data)
        self.assertEqual(result['status'], 'completed')
        self.assertIn('result', result)