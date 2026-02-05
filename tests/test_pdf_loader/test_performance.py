"""
PDF Loader性能测试
测试大文件处理和并发性能
"""

import time
import asyncio
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from apps.pdfloader.models import PDFDocument
from apps.mulvesdb.models import MulvesConnection


class PDFLoaderPerformanceTest(TestCase):
    """PDF Loader性能测试"""
    
    def setUp(self):
        """测试前置设置"""
        self.client = APIClient()
        self.milvus_connection = MulvesConnection.objects.create(
            name='perf_test_milvus',
            host='localhost',
            port=19530,
            database='perf_test_db',
            username='test_user',
            password='test_password',
            is_active=True
        )
        
        # 创建较大的测试内容
        self.large_text = "这是一段测试文本。" * 1000  # 约2万个字符
        self.test_pdf_content = self._create_large_pdf(self.large_text)
    
    def _create_large_pdf(self, text_content):
        """创建大型PDF内容"""
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
/Length {len(text_content) + 50}
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
    def test_large_pdf_processing_performance(self, mock_vector_service):
        """测试大PDF文件处理性能"""
        # Mock向量存储服务
        mock_storage_instance = MagicMock()
        mock_vector_service.return_value.__aenter__.return_value = mock_storage_instance
        mock_vector_service.return_value.__aexit__.return_value = None
        
        # Mock处理结果
        mock_storage_instance.store_pdf_chunks.return_value = {
            'success': True,
            'stored_count': 25,  # 大文件会产生更多分块
            'total_chunks': 25,
            'failed_count': 0
        }
        
        # 创建大文件上传
        large_file = SimpleUploadedFile(
            "large_test.pdf",
            self.test_pdf_content,
            content_type="application/pdf"
        )
        
        data = {
            'title': 'Large Performance Test Document',
            'file': large_file,
            'milvus_connection_id': self.milvus_connection.id,
            'collection_name': 'perf_test_collection'
        }
        
        # 记录处理时间
        start_time = time.time()
        
        response = self.client.post('/api/pdfloader/upload/', data, format='multipart')
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # 性能断言（应该在合理时间内完成）
        self.assertLess(processing_time, 10.0, "大文件上传处理时间过长")
        
        # 验证文档创建
        document = PDFDocument.objects.get(title='Large Performance Test Document')
        self.assertEqual(document.status, 'uploaded')
    
    @patch('apps.pdfloader.storage.PDFVectorStorageService')
    def test_concurrent_pdf_uploads(self, mock_vector_service):
        """测试并发PDF上传"""
        # Mock向量存储服务
        mock_storage_instance = MagicMock()
        mock_vector_service.return_value.__aenter__.return_value = mock_storage_instance
        mock_vector_service.return_value.__aexit__.return_value = None
        mock_storage_instance.store_pdf_chunks.return_value = {
            'success': True,
            'stored_count': 5,
            'total_chunks': 5,
            'failed_count': 0
        }
        
        # 准备多个测试文件
        test_files = []
        for i in range(3):
            test_file = SimpleUploadedFile(
                f"concurrent_test_{i}.pdf",
                self._create_simple_pdf(f"并发测试文档 {i}"),
                content_type="application/pdf"
            )
            test_files.append(test_file)
        
        # 并发上传测试
        async def concurrent_uploads():
            tasks = []
            for i, test_file in enumerate(test_files):
                data = {
                    'title': f'Concurrent Test Document {i}',
                    'file': test_file,
                    'milvus_connection_id': self.milvus_connection.id,
                    'collection_name': f'concurrent_test_collection_{i}'
                }
                
                # 使用async client进行并发请求
                task = asyncio.create_task(
                    self.async_post_request('/api/pdfloader/upload/', data)
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            return responses
        
        # 执行并发测试
        start_time = time.time()
        responses = asyncio.run(concurrent_uploads())
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # 验证所有请求都成功
        successful_responses = [r for r in responses if not isinstance(r, Exception)]
        self.assertEqual(len(successful_responses), 3, "并非所有并发请求都成功")
        
        # 验证处理时间合理性
        self.assertLess(total_time, 15.0, "并发处理时间过长")
        
        # 验证数据库记录
        documents = PDFDocument.objects.filter(
            title__startswith='Concurrent Test Document'
        )
        self.assertEqual(documents.count(), 3)
    
    async def async_post_request(self, url, data):
        """异步POST请求辅助方法"""
        # 这里简化处理，在实际测试中可以使用aiohttp或其他异步HTTP客户端
        from django.test import RequestFactory
        from apps.pdfloader.views import PDFUploadView
        
        factory = RequestFactory()
        request = factory.post(url, data)
        view = PDFUploadView.as_view()
        response = view(request)
        return response
    
    def _create_simple_pdf(self, text_content):
        """创建简单PDF"""
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


class PDFProcessorPerformanceTest(TestCase):
    """PDF处理器性能测试"""
    
    def test_chunking_performance(self):
        """测试分块性能"""
        from apps.pdfloader.pdf_processor import PDFProcessor
        
        # 创建大量文本
        large_text = "这是性能测试文本。\n" * 5000  # 约5万字符
        processor = PDFProcessor(chunk_size=1000, chunk_overlap=200)
        
        # 测试分块性能
        start_time = time.time()
        chunks = list(processor.chunk_text([{
            'page_number': 1,
            'text': large_text,
            'word_count': len(large_text.split())
        }]))
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # 验证结果和性能
        self.assertGreater(len(chunks), 0)
        self.assertLess(processing_time, 5.0, "分块处理时间过长")
        
        # 验证分块质量
        avg_chunk_size = sum(len(chunk.content) for chunk in chunks) / len(chunks)
        self.assertGreater(avg_chunk_size, 500)  # 平均分块大小应该合理
    
    def test_embedding_batch_performance(self):
        """测试批量embedding性能"""
        from apps.pdfloader.embedding import MockEmbeddingService
        
        # 创建大量文本进行embedding测试
        texts = [f"测试文本 {i}" for i in range(100)]
        embedding_service = MockEmbeddingService(dimensions=128)
        
        # 测试批量处理性能
        start_time = time.time()
        embeddings = embedding_service.embed_batch(texts, batch_size=20)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # 验证结果和性能
        self.assertEqual(len(embeddings), 100)
        self.assertLess(processing_time, 10.0, "批量embedding时间过长")
        
        # 验证embedding质量
        for embedding in embeddings:
            self.assertEqual(len(embedding.embedding), 128)
            self.assertTrue(all(isinstance(x, (int, float)) for x in embedding.embedding))


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])