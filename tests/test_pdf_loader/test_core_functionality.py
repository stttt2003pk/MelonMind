"""
PDF Loader 测试套件
测试PDF处理、embedding和向量存储功能
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from apps.pdfloader.models import PDFDocument, PDFChunk
from apps.mulvesdb.models import MulvesConnection


class PDFLoaderBaseTest(TestCase):
    """PDF Loader测试基类"""
    
    def setUp(self):
        """测试前置设置"""
        self.client = APIClient()
        
        # 创建测试用的Milvus连接
        self.milvus_connection = MulvesConnection.objects.create(
            name='test_milvus',
            host='localhost',
            port=19530,
            database='test_db',
            username='test_user',
            password='test_password',
            is_active=True
        )
        
        # 创建测试PDF文件内容（简单文本PDF）
        self.test_pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test PDF Content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000053 00000 n \n0000000115 00000 n \n0000000217 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n311\n%%EOF'


class PDFProcessorTest(PDFLoaderBaseTest):
    """PDF处理器测试"""
    
    def test_pdf_metadata_extraction(self):
        """测试PDF元数据提取"""
        from apps.pdfloader.pdf_processor import PDFMetadataExtractor
        
        # 创建临时PDF文件
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(self.test_pdf_content)
            temp_file_path = temp_file.name
        
        try:
            metadata = PDFMetadataExtractor.get_pdf_metadata(temp_file_path)
            
            self.assertEqual(metadata['file_path'], temp_file_path)
            self.assertGreater(metadata['file_size'], 0)
            self.assertIn('page_count', metadata)
            self.assertIn('is_encrypted', metadata)
            
        finally:
            os.unlink(temp_file_path)
    
    def test_pdf_text_extraction(self):
        """测试PDF文本提取"""
        from apps.pdfloader.pdf_processor import PDFProcessor
        
        # 创建临时PDF文件
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(self.test_pdf_content)
            temp_file_path = temp_file.name
        
        try:
            processor = PDFProcessor()
            pages_data = processor.extract_text_from_pdf(temp_file_path)
            
            # 注意：由于这是一个简化的PDF，可能提取不到文本
            # 但我们测试处理流程是否正常
            self.assertIsInstance(pages_data, list)
            
        finally:
            os.unlink(temp_file_path)
    
    def test_invalid_pdf_handling(self):
        """测试无效PDF文件处理"""
        from apps.pdfloader.pdf_processor import PDFProcessor
        
        processor = PDFProcessor()
        
        # 测试不存在的文件
        with self.assertRaises(FileNotFoundError):
            processor.extract_text_from_pdf('/nonexistent/file.pdf')
        
        # 测试非PDF文件 - PyPDF2会静默处理这种情况
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b'This is not a PDF file')
            temp_file_path = temp_file.name
        
        try:
            # 对于非PDF文件，process_pdf应该能处理但可能返回空结果
            result = list(processor.process_pdf(temp_file_path))
            # 不应该抛出异常，但结果可能是空的
            self.assertIsInstance(result, list)
        finally:
            os.unlink(temp_file_path)


class EmbeddingServiceTest(PDFLoaderBaseTest):
    """Embedding服务测试"""
    
    def test_mock_embedding_service(self):
        """测试Mock Embedding服务"""
        from apps.pdfloader.embedding import MockEmbeddingService
        
        service = MockEmbeddingService(dimensions=128)
        
        # 测试单个文本embedding
        result = service.embed_text("Hello world")
        self.assertEqual(len(result.embedding), 128)
        self.assertEqual(result.text, "Hello world")
        self.assertEqual(result.model, "mock-embedding")
        
        # 测试批量embedding
        texts = ["Hello", "World", "Test"]
        results = service.embed_batch(texts)
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertEqual(len(result.embedding), 128)
    
    def test_embedding_validation(self):
        """测试embedding验证"""
        from apps.pdfloader.embedding import MockEmbeddingService
        
        service = MockEmbeddingService(dimensions=4)
        result = service.embed_text("test")
        
        # 测试有效embedding
        self.assertTrue(service.validate_embedding([1.0, 2.0, 3.0, 4.0]))
        
        # 测试无效embedding
        self.assertFalse(service.validate_embedding([1.0, float('nan'), 3.0, 4.0]))
        self.assertFalse(service.validate_embedding([1.0, 2.0, 3.0]))  # 维度不匹配
        self.assertFalse(service.validate_embedding("not_a_list"))


class PDFDocumentModelTest(PDFLoaderBaseTest):
    """PDF文档模型测试"""
    
    def test_pdf_document_creation(self):
        """测试PDF文档创建"""
        document = PDFDocument.objects.create(
            title='Test Document',
            file_path='/path/to/test.pdf',
            file_size=1024,
            page_count=5,
            milvus_connection=self.milvus_connection,
            collection_name='test_collection'
        )
        
        self.assertEqual(document.title, 'Test Document')
        self.assertEqual(document.status, 'uploaded')
        self.assertEqual(str(document), 'Test Document (/path/to/test.pdf)')
    
    def test_document_status_transitions(self):
        """测试文档状态转换"""
        document = PDFDocument.objects.create(
            title='Test Document',
            file_path='/path/to/test.pdf',
            file_size=1024,
            page_count=5,
            milvus_connection=self.milvus_connection,
            collection_name='test_collection'
        )
        
        # 测试处理中状态
        document.mark_as_processing()
        self.assertEqual(document.status, 'processing')
        
        # 测试完成状态
        document.mark_as_completed()
        self.assertEqual(document.status, 'completed')
        self.assertIsNotNone(document.processed_at)
        
        # 测试失败状态
        document.mark_as_failed('Test error')
        self.assertEqual(document.status, 'failed')
        self.assertEqual(document.error_message, 'Test error')


class PDFLoaderAPITest(PDFLoaderBaseTest):
    """PDF Loader API测试"""
    
    def test_upload_pdf_endpoint(self):
        """测试PDF上传端点"""
        # 创建测试PDF文件
        test_file = SimpleUploadedFile(
            "test.pdf",
            self.test_pdf_content,
            content_type="application/pdf"
        )
        
        data = {
            'title': 'Test PDF Document',
            'file': test_file,
            'milvus_connection_id': self.milvus_connection.id,
            'collection_name': 'test_api_collection'
        }
        
        # Mock异步处理函数
        with patch('apps.pdfloader.views.asyncio.create_task') as mock_task:
            response = self.client.post('/api/pdfloader/upload/', data, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertTrue(response.data['success'])
            
            # 验证文档已创建
            document = PDFDocument.objects.get(title='Test PDF Document')
            self.assertEqual(document.status, 'uploaded')
            
            # 验证异步任务被调用
            mock_task.assert_called_once()
    
    def test_list_documents_endpoint(self):
        """测试文档列表端点"""
        # 创建测试文档
        PDFDocument.objects.create(
            title='Document 1',
            file_path='/path/to/doc1.pdf',
            file_size=1024,
            page_count=5,
            milvus_connection=self.milvus_connection,
            collection_name='test_collection1'
        )
        
        PDFDocument.objects.create(
            title='Document 2',
            file_path='/path/to/doc2.pdf',
            file_size=2048,
            page_count=10,
            milvus_connection=self.milvus_connection,
            collection_name='test_collection2'
        )
        
        response = self.client.get('/api/pdfloader/documents/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_get_document_detail(self):
        """测试获取文档详情"""
        document = PDFDocument.objects.create(
            title='Test Document',
            file_path='/path/to/test.pdf',
            file_size=1024,
            page_count=5,
            milvus_connection=self.milvus_connection,
            collection_name='test_collection'
        )
        
        response = self.client.get(f'/api/pdfloader/documents/{document.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Document')
    
    def test_invalid_upload(self):
        """测试无效上传"""
        # 测试缺少必需字段
        data = {
            'title': 'Test Document'
            # 缺少file, milvus_connection_id, collection_name
        }
        
        response = self.client.post('/api/pdfloader/upload/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # 测试非PDF文件
        txt_file = SimpleUploadedFile(
            "test.txt",
            b"This is a text file",
            content_type="text/plain"
        )
        
        data = {
            'title': 'Invalid Document',
            'file': txt_file,
            'milvus_connection_id': self.milvus_connection.id,
            'collection_name': 'test_collection'
        }
        
        response = self.client.post('/api/pdfloader/upload/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])