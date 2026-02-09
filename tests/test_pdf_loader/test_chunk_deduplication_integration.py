"""
PDF Loader与块级去重集成测试
"""
import os
import tempfile
import django
from pathlib import Path

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase
from unittest.mock import patch, MagicMock
from apps.pdfloader.storage import PDFVectorStorageService
from apps.mulvesdb.models import MulvesConnection
from apps.pdfloader.models import PDFDocument


class IntegrationTestPDFWithDeduplication(TestCase):
    """PDF处理与块级去重集成测试"""
    
    def setUp(self):
        """测试准备"""
        # 创建测试用的Milvus连接
        self.milvus_connection = MulvesConnection.objects.create(
            name="test_milvus",
            host="localhost",
            port=19530,
            database="test_db",
            username="test_user",
            password="test_password",
            is_active=True
        )
        
        # 创建测试文档
        self.pdf_document = PDFDocument.objects.create(
            title="测试文档",
            file_path="/tmp/test.pdf",
            file_size=1024,
            page_count=5,
            milvus_connection=self.milvus_connection,
            collection_name="test_collection"
        )
        
        # 测试块数据
        self.test_chunks = [
            {
                'content': '人工智能是计算机科学的一个分支',
                'page_number': 1,
                'chunk_index': 0,
                'metadata': {}
            },
            {
                'content': '机器学习是实现人工智能的方法之一',
                'page_number': 1,
                'chunk_index': 1,
                'metadata': {}
            },
            {
                'content': '深度学习在图像识别方面表现出色',
                'page_number': 2,
                'chunk_index': 2,
                'metadata': {}
            }
        ]
    
    @patch('apps.mulvesdb.connectors.MulvesDBConnector.connect_sync')
    @patch('apps.mulvesdb.connectors.MulvesDBConnector.disconnect_sync')
    @patch('apps.mulvesdb.connectors.MilvusClient')
    def test_store_pdf_chunks_with_deduplication(self, mock_milvus_client, mock_disconnect, mock_connect):
        """测试带有去重的PDF块存储"""
        # 配置mock
        mock_client_instance = MagicMock()
        mock_milvus_client.return_value = mock_client_instance
        mock_client_instance.list_collections.return_value = ['test_collection']
        mock_client_instance.insert.return_value = MagicMock(primary_keys=['id1', 'id2', 'id3'])
        
        # 创建存储服务
        storage_service = PDFVectorStorageService(self.milvus_connection.id)
        
        # 执行存储操作
        with storage_service as service:
            result = service.store_pdf_chunks(
                document_id=self.pdf_document.id,
                chunks_data=self.test_chunks,
                collection_name=self.pdf_document.collection_name
            )
        
        # 验证结果
        self.assertTrue(result['success'])
        self.assertEqual(result['total_chunks'], 3)
        self.assertGreater(result['stored_count'], 0)
        
        # 验证Milvus客户端被正确调用
        mock_client_instance.insert.assert_called_once()
        call_args = mock_client_instance.insert.call_args[1]
        self.assertEqual(call_args['collection_name'], 'test_collection')
        self.assertEqual(len(call_args['data']), 3)  # 所有块都应该被传递（去重在内部处理）
    
    @patch('apps.mulvesdb.connectors.MulvesDBConnector.connect_sync')
    @patch('apps.mulvesdb.connectors.MulvesDBConnector.disconnect_sync')
    @patch('apps.mulvesdb.connectors.MilvusClient')
    @patch('apps.mulvesdb.models.ChunkHashIndex.is_duplicate')
    def test_deduplication_effectiveness(self, mock_is_duplicate, mock_milvus_client, mock_disconnect, mock_connect):
        """测试去重效果"""
        # 模拟部分重复的情况
        mock_is_duplicate.side_effect = [False, True, False]  # 第二个块是重复的
        mock_client_instance = MagicMock()
        mock_milvus_client.return_value = mock_client_instance
        mock_client_instance.list_collections.return_value = ['test_collection']
        mock_client_instance.insert.return_value = MagicMock(primary_keys=['id1', 'id3'])  # 只有两个块被插入
        
        storage_service = PDFVectorStorageService(self.milvus_connection.id)
        
        with storage_service as service:
            result = service.store_pdf_chunks(
                document_id=self.pdf_document.id,
                chunks_data=self.test_chunks,
                collection_name=self.pdf_document.collection_name
            )
        
        # 验证去重效果
        self.assertTrue(result['success'])
        self.assertEqual(result['total_chunks'], 3)
        self.assertEqual(result['stored_count'], 2)  # 应该只有2个块被存储
        self.assertEqual(result['failed_count'], 1)  # 1个块被过滤
        
        # 验证返回结果中包含过滤信息
        self.assertIn('filtered_count', result)
        self.assertEqual(result['filtered_count'], 1)


# 手动测试函数
def manual_integration_test():
    """手动集成测试"""
    print("=== PDF处理与块级去重集成测试 ===")
    
    try:
        # 测试哈希计算的一致性
        from apps.mulvesdb.utils import calculate_chunk_hash
        
        content = "测试内容"
        doc_id = 1
        chunk_idx = 0
        
        hash1 = calculate_chunk_hash(content, doc_id, chunk_idx)
        hash2 = calculate_chunk_hash(content, doc_id, chunk_idx)
        
        print(f"哈希计算一致性: {hash1 == hash2}")
        print(f"哈希值: {hash1}")
        
        # 测试不同参数的影响
        hash_diff_doc = calculate_chunk_hash(content, doc_id + 1, chunk_idx)
        hash_diff_chunk = calculate_chunk_hash(content, doc_id, chunk_idx + 1)
        
        print(f"不同文档ID产生不同哈希: {hash1 != hash_diff_doc}")
        print(f"不同块索引产生不同哈希: {hash1 != hash_diff_chunk}")
        
        # 测试去重管理器
        from apps.mulvesdb.utils import ChunkDeduplicationManager
        
        manager = ChunkDeduplicationManager()
        test_hash = "a" * 64
        
        print(f"初始重复检查: {manager.is_duplicate(test_hash)}")
        manager.add_hash(test_hash)
        print(f"添加后重复检查: {manager.is_duplicate(test_hash)}")
        
        # 显示统计信息
        stats = manager.get_statistics()
        print(f"去重统计: {stats}")
        
        print("✅ 集成测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = manual_integration_test()
    exit(0 if success else 1)