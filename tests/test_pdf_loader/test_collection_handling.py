"""
PDF Loader 集合处理测试
测试集合参数的可选性和存在性检查功能
"""

import os
import tempfile
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock
from apps.pdfloader.models import PDFDocument, PDFCollectionConfig
from apps.mulvesdb.models import MulvesConnection


class PDFCollectionHandlingTest(TestCase):
    """PDF集合处理功能测试"""
    
    def setUp(self):
        """测试初始化"""
        self.client = APIClient()
        
        # 创建测试用的Milvus连接
        self.milvus_connection = MulvesConnection.objects.create(
            name='Test Connection',
            host='localhost',
            port=19530,
            database='default',
            is_active=True
        )
        
        # 创建测试用的集合配置
        self.collection_config = PDFCollectionConfig.objects.create(
            name='test_config',
            description='测试集合配置',
            milvus_connection=self.milvus_connection,
            milvus_collection_name='test_collection',
            is_active=True,
            is_default=False
        )
        
        # 创建测试PDF文件
        self.test_pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Hello World) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000053 00000 n \n0000000115 00000 n \n0000000203 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n299\n%%EOF'
        
        # 创建临时PDF文件
        self.temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        self.temp_pdf.write(self.test_pdf_content)
        self.temp_pdf.close()
    
    def tearDown(self):
        """测试清理"""
        # 删除临时文件
        if os.path.exists(self.temp_pdf.name):
            os.unlink(self.temp_pdf.name)
    
    @patch('apps.pdfloader.storage.PDFVectorStorageService')
    @patch('apps.pdfloader.views.PDFProcessingPipeline')
    def test_upload_without_collection_params_uses_test_collection(self, mock_pipeline, mock_storage_service):
        """测试不提供集合参数时使用test集合"""
        # 配置mock
        mock_storage_instance = MagicMock()
        mock_storage_instance.milvus_connector.collection_exists_sync.return_value = True
        mock_storage_service.return_value.__enter__.return_value = mock_storage_instance
        
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.process_pdf_document.return_value = {
            'success': True,
            'document_id': 1,
            'chunks_processed': 3,
            'chunks_stored': 3
        }
        mock_pipeline.return_value = mock_pipeline_instance
        
        # 准备上传数据（不包含collection参数）
        with open(self.temp_pdf.name, 'rb') as pdf_file:
            data = {
                'title': 'Test Document',
                'file': pdf_file,
                'milvus_connection_id': self.milvus_connection.id
            }
            
            response = self.client.post(
                reverse('pdfloader:pdf-upload'),
                data,
                format='multipart'
            )
        
        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        
        # 验证文档使用了test集合
        document = PDFDocument.objects.get(id=response_data['data']['id'])
        self.assertEqual(document.collection_name, 'test')
        
        # 验证mock被正确调用
        mock_storage_instance.milvus_connector.collection_exists_sync.assert_called_with('test')
    
    @patch('apps.pdfloader.storage.PDFVectorStorageService')
    @patch('apps.pdfloader.views.PDFProcessingPipeline')
    def test_upload_with_collection_config_id(self, mock_pipeline, mock_storage_service):
        """测试使用collection_config_id参数"""
        # 配置mock
        mock_storage_instance = MagicMock()
        mock_storage_instance.milvus_connector.collection_exists_sync.return_value = True
        mock_storage_service.return_value.__enter__.return_value = mock_storage_instance
        
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.process_pdf_document.return_value = {
            'success': True,
            'document_id': 1,
            'chunks_processed': 3,
            'chunks_stored': 3
        }
        mock_pipeline.return_value = mock_pipeline_instance
        
        # 准备上传数据（使用collection_config_id）
        with open(self.temp_pdf.name, 'rb') as pdf_file:
            data = {
                'title': 'Test Document',
                'file': pdf_file,
                'milvus_connection_id': self.milvus_connection.id,
                'collection_config_id': self.collection_config.id
            }
            
            response = self.client.post(
                reverse('pdfloader:pdf-upload'),
                data,
                format='multipart'
            )
        
        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        
        # 验证文档使用了正确的集合名称
        document = PDFDocument.objects.get(id=response_data['data']['id'])
        self.assertEqual(document.collection_name, 'test_collection')
    
    @patch('apps.pdfloader.storage.PDFVectorStorageService')
    @patch('apps.pdfloader.views.PDFProcessingPipeline')
    def test_upload_with_custom_collection_name(self, mock_pipeline, mock_storage_service):
        """测试使用自定义collection_name参数"""
        # 配置mock
        mock_storage_instance = MagicMock()
        mock_storage_instance.milvus_connector.collection_exists_sync.return_value = True
        mock_storage_service.return_value.__enter__.return_value = mock_storage_instance
        
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.process_pdf_document.return_value = {
            'success': True,
            'document_id': 1,
            'chunks_processed': 3,
            'chunks_stored': 3
        }
        mock_pipeline.return_value = mock_pipeline_instance
        
        # 准备上传数据（使用自定义collection_name）
        with open(self.temp_pdf.name, 'rb') as pdf_file:
            data = {
                'title': 'Test Document',
                'file': pdf_file,
                'milvus_connection_id': self.milvus_connection.id,
                'collection_name': 'custom_collection'
            }
            
            response = self.client.post(
                reverse('pdfloader:pdf-upload'),
                data,
                format='multipart'
            )
        
        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        
        # 验证文档使用了自定义集合名称
        document = PDFDocument.objects.get(id=response_data['data']['id'])
        self.assertEqual(document.collection_name, 'custom_collection')
    
    @patch('apps.pdfloader.storage.PDFVectorStorageService')
    def test_upload_fails_when_test_collection_not_exists(self, mock_storage_service):
        """测试test集合不存在时上传失败"""
        # 配置mock，让test集合不存在
        mock_storage_instance = MagicMock()
        mock_storage_instance.milvus_connector.collection_exists_sync.return_value = False
        mock_storage_service.return_value.__enter__.return_value = mock_storage_instance
        
        # 准备上传数据（不包含collection参数，应该使用默认的test集合）
        with open(self.temp_pdf.name, 'rb') as pdf_file:
            data = {
                'title': 'Test Document',
                'file': pdf_file,
                'milvus_connection_id': self.milvus_connection.id
            }
            
            response = self.client.post(
                reverse('pdfloader:pdf-upload'),
                data,
                format='multipart'
            )
        
        # 验证响应是错误状态
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertIn('test', response_data['message'])
        self.assertIn('不存在', response_data['message'])
    
    @patch('apps.pdfloader.storage.PDFVectorStorageService')
    def test_upload_fails_when_custom_collection_not_exists(self, mock_storage_service):
        """测试自定义集合不存在时上传失败"""
        # 配置mock，让自定义集合不存在
        mock_storage_instance = MagicMock()
        mock_storage_instance.milvus_connector.collection_exists_sync.return_value = False
        mock_storage_service.return_value.__enter__.return_value = mock_storage_instance
        
        # 准备上传数据（使用不存在的自定义集合）
        with open(self.temp_pdf.name, 'rb') as pdf_file:
            data = {
                'title': 'Test Document',
                'file': pdf_file,
                'milvus_connection_id': self.milvus_connection.id,
                'collection_name': 'nonexistent_collection'
            }
            
            response = self.client.post(
                reverse('pdfloader:pdf-upload'),
                data,
                format='multipart'
            )
        
        # 验证响应是错误状态
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertIn('nonexistent_collection', response_data['message'])
        self.assertIn('不存在', response_data['message'])
    
    def test_invalid_collection_config_id_returns_error(self):
        """测试无效的collection_config_id返回错误"""
        with open(self.temp_pdf.name, 'rb') as pdf_file:
            data = {
                'title': 'Test Document',
                'file': pdf_file,
                'milvus_connection_id': self.milvus_connection.id,
                'collection_config_id': 99999  # 不存在的ID
            }
            
            response = self.client.post(
                reverse('pdfloader:pdf-upload'),
                data,
                format='multipart'
            )
        
        # 验证响应是错误状态
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertIn('集合配置', response_data['message'])
    
    def test_invalid_collection_name_format_returns_error(self):
        """测试无效的集合名称格式返回错误"""
        invalid_names = [
            '123invalid',  # 不能以数字开头
            'invalid-name',  # 不能包含连字符
            'invalid name',  # 不能包含空格
            '',  # 空字符串
        ]
        
        for invalid_name in invalid_names:
            with open(self.temp_pdf.name, 'rb') as pdf_file:
                data = {
                    'title': 'Test Document',
                    'file': pdf_file,
                    'milvus_connection_id': self.milvus_connection.id,
                    'collection_name': invalid_name
                }
                
                response = self.client.post(
                    reverse('pdfloader:pdf-upload'),
                    data,
                    format='multipart'
                )
            
            # 验证响应是错误状态
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            response_data = response.json()
            self.assertFalse(response_data['success'])
            self.assertIn('集合名称', response_data['message'])


if __name__ == '__main__':
    import django
    from django.test.utils import get_runner
    from django.conf import settings
    
    django.setup()
    
    # 运行测试
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['tests.test_pdf_loader.test_collection_handling'])
    
    if failures:
        exit(1)
    else:
        print("所有集合处理测试通过!")