import pytest
from django.test import TestCase
from apps.agents.flows.base_flow import NetworkOperationsFlow


class TestNetworkOperationsFlow(TestCase):
    """Test network operations flow"""
    
    def setUp(self):
        self.flow = NetworkOperationsFlow()
    
    def test_validate_input_valid(self):
        """Test input validation - valid input"""
        input_data = {
            'operation_type': 'health_check',
            'target_device': {'ip': '192.168.1.1'}
        }
        self.assertTrue(self.flow.validate_input(input_data))
    
    def test_execute_health_check(self):
        """Test health check execution"""
        input_data = {
            'operation_type': 'health_check',
            'target_device': {'ip': '192.168.1.1'}
        }
        
        result = self.flow.execute(input_data)
        self.assertEqual(result['status'], 'completed')
        self.assertIn('result', result)
    
    def test_execute_backup_configuration(self):
        """Test configuration backup execution"""
        input_data = {
            'operation_type': 'configuration_backup',
            'target_device': {'ip': '192.168.1.1'}
        }
        
        result = self.flow.execute(input_data)
        self.assertEqual(result['status'], 'completed')
        self.assertIn('result', result)