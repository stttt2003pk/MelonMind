import pytest
from unittest.mock import patch, MagicMock
from apps.knowledge_base.connectors.mulves_client import MulvesClient


class TestMulvesClient:
    """测试 Mulves 客户端"""
    
    def setup_method(self):
        self.client = MulvesClient()
    
    @patch('apps.knowledge_base.connectors.mulves_client.MulvesClient.search')
    def test_search_success(self, mock_search):
        """测试搜索功能成功"""
        mock_search.return_value = [
            {
                'id': 'test_001',
                'title': '测试条目',
                'content': '测试内容',
                'category': 'test',
                'relevance_score': 0.95
            }
        ]
        
        results = self.client.search('测试查询')
        assert len(results) == 1
        assert results[0]['id'] == 'test_001'
        assert results[0]['title'] == '测试条目'
    
    def test_search_empty_query(self):
        """测试空查询"""
        with pytest.raises(Exception):
            self.client.search('')
    
    @patch('apps.knowledge_base.connectors.mulves_client.MulvesClient.get_entry')
    def test_get_entry(self, mock_get_entry):
        """测试获取条目"""
        mock_get_entry.return_value = {
            'id': 'test_001',
            'title': '测试条目',
            'content': '测试内容'
        }
        
        entry = self.client.get_entry('test_001')
        assert entry['id'] == 'test_001'
        assert entry['title'] == '测试条目'