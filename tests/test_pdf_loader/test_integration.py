"""
PDF Loader集成测试
测试完整的PDF处理流程
"""

import os
import tempfile
import asyncio
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from apps.pdfloader.models import PDFDocument, PDFChunk
from apps.mulvesdb.models import MulvesConnection


class PDFLoaderIntegrationTest(TestCase):
    """PDF Loader集成测试"""
    
    def setUp(self):
        """测试前置设置"""
        self.client = APIClient()
        
        # 创建测试用的Milvus连接
        self.milvus_connection = MulvesConnection.objects.create(
            name='integration_test_milvus',
            host='localhost',
            port=19530,
            database='integration_test_db',
            username='test_user',
            password='test_password',
            is_active=True
        )
        
        # 创建更真实的测试PDF内容
        self.sample_text = """
        这是一个测试PDF文档。
        它包含多行文本内容用于测试分块功能。
        第一行内容在这里。
        第二行内容在这里。
        第三行内容在这里。
        第四行内容在这里。
        第五行内容在这里。
        第六行内容在这里。
        第七行内容在这里。
        第八行内容在这里。
        """
        
        self.test_pdf_content = self._create_simple_pdf(self.sample_text)
    
    def _create_simple_pdf(self, text_content):
        """创建简单的PDF内容"""
        # 这是一个非常简化的PDF结构，实际使用中应该使用PyPDF2或其他库生成真实PDF
        pdf_template = f"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj
4 0 obj
<<
/Length {len(text_content) + 20}
>>
stream
BT
/F1 12 Tf
72 720 Td
({text_content}) Tj
ET
endstream
endobj
5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj
xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000115 00000 n 
0000000247 00000 n 
0000000400 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
500
%%EOF"""
        return pdf_template.encode('utf-8')
    
    @patch('apps.pdfloader.storage.PDFVectorStorageService')
    @patch('apps.pdfloader.views.asyncio.create_task')
    def test_complete_pdf_processing_flow(self, mock_create_task, mock_vector_service):
        """测试完整的PDF处理流程"""
        # Mock向量存储服务
        mock_storage_instance = MagicMock()
        mock_vector_service.return_value.__aenter__.return_value = mock_storage_instance
        mock_vector_service.return_value.__aexit__.return_value = None
        
        # Mock处理结果
        mock_storage_instance.store_pdf_chunks.return_value = {
            'success': True,
            'stored_count': 3,
            'total_chunks': 3,
            'failed_count': 0
        }
        
        # 创建上传文件
        test_file = SimpleUploadedFile(
            "integration_test.pdf",
            self.test_pdf_content,
            content_type="application/pdf"
        )
        
        data = {
            'title': 'Integration Test Document',
            'file': test_file,
            'milvus_connection_id': self.milvus_connection.id,
            'collection_name': 'integration_test_collection'
        }
        
        # 执行上传
        response = self.client.post('/api/pdfloader/upload/', data, format='multipart')
        
        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # 验证文档创建
        document = PDFDocument.objects.get(title='Integration Test Document')
        self.assertEqual(document.status, 'uploaded')
        self.assertEqual(document.milvus_connection, self.milvus_connection)
        self.assertEqual(document.collection_name, 'integration_test_collection')
        
        # 验证异步任务创建
        mock_create_task.assert_called_once()
    
    def test_vector_search_endpoint(self):
        """测试向量搜索端点"""
        data = {
            'query_text': '测试搜索内容',
            'collection_name': 'test_collection',
            'limit': 5
        }
        
        # Mock Milvus连接和搜索结果
        with patch('apps.pdfloader.views.MulvesConnection') as mock_connection, \
             patch('apps.pdfloader.storage.PDFVectorStorageService') as mock_storage:
            
            # Mock连接查询
            mock_active_connection = MagicMock()
            mock_active_connection.id = 1
            mock_connection.objects.filter.return_value.afirst.return_value = mock_active_connection
            
            # Mock存储服务
            mock_storage_instance = MagicMock()
            mock_storage.return_value.__aenter__.return_value = mock_storage_instance
            mock_storage.return_value.__aexit__.return_value = None
            
            # Mock搜索结果
            mock_storage_instance.search_similar_chunks.return_value = [
                {
                    'id': 1,
                    'content': '找到的相关内容1',
                    'distance': 0.1
                },
                {
                    'id': 2,
                    'content': '找到的相关内容2', 
                    'distance': 0.2
                }
            ]
            
            response = self.client.post('/api/pdfloader/search/', data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['success'])
            self.assertEqual(len(response.data['data']), 2)
    
    def test_processing_status_check(self):
        """测试处理状态查询"""
        # 创建不同状态的文档
        document1 = PDFDocument.objects.create(
            title='Completed Document',
            file_path='/path/to/completed.pdf',
            file_size=1024,
            page_count=5,
            milvus_connection=self.milvus_connection,
            collection_name='test_collection',
            status='completed'
        )
        
        document2 = PDFDocument.objects.create(
            title='Failed Document',
            file_path='/path/to/failed.pdf',
            file_size=2048,
            page_count=10,
            milvus_connection=self.milvus_connection,
            collection_name='test_collection',
            status='failed',
            error_message='Processing failed'
        )
        
        # 添加一些分块数据
        PDFChunk.objects.create(
            document=document1,
            chunk_index=0,
            content='Chunk 1 content',
            page_number=1,
            vector_id='vector_1'
        )
        
        PDFChunk.objects.create(
            document=document1,
            chunk_index=1,
            content='Chunk 2 content',
            page_number=1,
            vector_id='vector_2'
        )
        
        # 测试完成文档的状态
        response = self.client.get(f'/api/pdfloader/documents/{document1.id}/status/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['status'], 'completed')
        self.assertEqual(response.data['data']['chunks_count'], 2)
        self.assertEqual(response.data['data']['success_rate'], 100.0)
        
        # 测试失败文档的状态
        response = self.client.get(f'/api/pdfloader/documents/{document2.id}/status/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['status'], 'failed')
        self.assertEqual(response.data['data']['error_message'], 'Processing failed')


class PDFProcessorIntegrationTest(TestCase):
    """PDF处理器集成测试"""
    
    def setUp(self):
        self.sample_text = "这是第一段文本。\n这是第二段文本。\n这是第三段文本。"
        self.test_pdf_content = self._create_simple_pdf(self.sample_text)
    
    def _create_simple_pdf(self, text_content):
        """创建测试PDF"""
        pdf_template = f"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length {len(text_content) + 20}
>>
stream
BT
/F1 12 Tf
72 720 Td
({text_content}) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000115 00000 n 
0000000217 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
311
%%EOF"""
        return pdf_template.encode('utf-8')
    
    def test_pdf_processing_pipeline_with_real_data(self):
        """使用真实数据测试PDF处理管道"""
        from apps.pdfloader.pdf_processor import PDFProcessor
        from apps.pdfloader.embedding import MockEmbeddingService
        
        # 创建临时PDF文件
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(self.test_pdf_content)
            temp_file_path = temp_file.name
        
        try:
            # 测试PDF处理器
            processor = PDFProcessor(chunk_size=50, chunk_overlap=10)
            chunks = list(processor.process_pdf(temp_file_path))
            
            # 验证分块结果
            self.assertGreater(len(chunks), 0)
            for chunk in chunks:
                self.assertIsInstance(chunk.content, str)
                self.assertGreater(len(chunk.content), 0)
                self.assertIsInstance(chunk.page_number, int)
                self.assertIsInstance(chunk.chunk_index, int)
            
            # 测试embedding服务
            embedding_service = MockEmbeddingService(dimensions=128)
            texts = [chunk.content for chunk in chunks[:2]]  # 取前两个分块测试
            embeddings = embedding_service.embed_batch(texts)
            
            self.assertEqual(len(embeddings), len(texts))
            for embedding in embeddings:
                self.assertEqual(len(embedding.embedding), 128)
                self.assertTrue(embedding_service.validate_embedding(embedding.embedding))
                
        finally:
            os.unlink(temp_file_path)


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '-s'])