import pytest
from unittest.mock import patch, MagicMock
from apps.knowledge_base.connectors.mulves_client import MulvesClient


class TestMulvesClient:
    """Test Mulves client"""
    
    def setup_method(self):
        self.client = MulvesClient()
    
    @patch('apps.knowledge_base.connectors.mulves_client.MulvesClient.search')
    def test_search_success(self, mock_search):
        """Test search function success"""
        mock_search.return_value = [
            {
                'id': 'test_001',
                'title': 'Test Entry',
                'content': 'Test Content',
                'category': 'test',
                'relevance_score': 0.95
            }
        ]
        
        results = self.client.search('Test Query')
        assert len(results) == 1
        assert results[0]['id'] == 'test_001'
        assert results[0]['title'] == 'Test Entry'
    
    def test_search_empty_query(self):
        """Test empty query"""
        with pytest.raises(Exception):
            self.client.search('')
    
    @patch('apps.knowledge_base.connectors.mulves_client.MulvesClient.get_entry')
    def test_get_entry(self, mock_get_entry):
        """Test get entry"""
        mock_get_entry.return_value = {
            'id': 'test_001',
            'title': 'Test Entry',
            'content': 'Test Content'
        }
        
        entry = self.client.get_entry('test_001')
        assert entry['id'] == 'test_001'
        assert entry['title'] == 'Test Entry'