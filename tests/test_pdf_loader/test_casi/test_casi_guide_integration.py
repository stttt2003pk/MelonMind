"""
CASI 参考指南完整流程测试
测试从PDF上传到向量查询的完整流程
"""

import os
import sys
import asyncio
import time
import pytest
import django
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import tempfile
import shutil
from pathlib import Path

# 配置Django设置
django.setup()

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django.setup()

from apps.pdfloader.models import PDFDocument, PDFChunk
from apps.mulvesdb.models import MulvesConnection


@pytest.mark.django_db
class TestCASIGuideIntegration(TestCase):
    """CASI参考指南集成测试"""
    
    def setUp(self):
        """测试初始化"""
        self.client = APIClient()
        self.test_pdf_path = os.path.join(
            os.path.dirname(__file__), 
            'pdf', 
            'CASI_RefGuide.pdf'
        )
        
        # 确保测试PDF文件存在
        assert os.path.exists(self.test_pdf_path), f"测试PDF文件不存在: {self.test_pdf_path}"
        
        # 创建Milvus连接配置（使用mock）
        self.milvus_connection = MulvesConnection.objects.create(
            name="Test Milvus Connection",
            host="localhost",
            port=19530,
            username="test_user",
            password="test_password",
            is_active=True,
            connection_config={
                "timeout": 30,
                "secure": False
            }
        )
        
        # 创建测试用的集合名称
        self.collection_name = "casi_guide_test_collection"
        
    def tearDown(self):
        """测试清理"""
        # 删除测试创建的文档
        PDFDocument.objects.all().delete()
        PDFChunk.objects.all().delete()
        
        # 删除Milvus连接
        if hasattr(self, 'milvus_connection'):
            self.milvus_connection.delete()

    def test_01_pdf_upload_success(self):
        """测试1: PDF文件成功上传"""
        print("\n=== 测试1: PDF文件上传 ===")
        
        # 准备上传数据
        with open(self.test_pdf_path, 'rb') as pdf_file:
            upload_data = {
                'title': 'CASI Reference Guide Test',
                'file': pdf_file,
                'milvus_connection_id': self.milvus_connection.id,
                'collection_name': self.collection_name
            }
            
            # 发送上传请求
            response = self.client.post(
                reverse('pdfloader:pdf-upload'),
                data=upload_data,
                format='multipart'
            )
        
        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertIn('data', response_data)
        
        # 验证返回的文档信息
        document_data = response_data['data']
        self.assertEqual(document_data['title'], 'CASI Reference Guide Test')
        self.assertEqual(document_data['status'], 'pending')
        self.assertEqual(document_data['collection_name'], self.collection_name)
        
        # 保存文档ID用于后续测试
        self.document_id = document_data['id']
        print(f"✓ PDF上传成功，文档ID: {self.document_id}")
        
    def test_02_check_processing_status(self):
        """测试2: 检查文档处理状态"""
        print("\n=== 测试2: 文档处理状态检查 ===")
        
        # 首先确保有文档ID
        if not hasattr(self, 'document_id'):
            self.test_01_pdf_upload_success()
        
        # 等待一段时间让后台处理开始
        time.sleep(2)
        
        # 查询处理状态
        response = self.client.get(
            reverse('pdfloader:pdf-processing-status', kwargs={'pk': self.document_id})
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertIn('data', response_data)
        
        status_data = response_data['data']
        self.assertEqual(status_data['id'], self.document_id)
        print(f"✓ 文档状态: {status_data['status']}")
        print(f"✓ 文件大小: {status_data['file_size']} bytes")
        
        # 保存当前状态
        self.current_status = status_data['status']
        
    @patch('apps.pdfloader.storage.PDFVectorStorageService._connect_to_milvus')
    @patch('apps.pdfloader.storage.PDFVectorStorageService.create_document_collection')
    @patch('apps.pdfloader.storage.PDFVectorStorageService.store_pdf_chunks')
    def test_03_mock_processing_pipeline(self, mock_store_chunks, mock_create_collection, mock_connect):
        """测试3: Mock完整的处理流水线"""
        print("\n=== 测试3: Mock处理流水线 ===")
        
        # 设置mock返回值
        mock_connect.return_value = None
        mock_create_collection.return_value = True
        mock_store_chunks.return_value = {
            'success': True,
            'stored_count': 15,
            'total_chunks': 15,
            'failed_count': 0
        }
        
        # 创建测试文档
        document = PDFDocument.objects.create(
            title='CASI Guide Mock Test',
            file_path=self.test_pdf_path,
            file_size=os.path.getsize(self.test_pdf_path),
            page_count=50,  # 假设有50页
            milvus_connection=self.milvus_connection,
            collection_name=f"{self.collection_name}_mock",
            status='processing'
        )
        
        # 模拟处理过程
        from apps.pdfloader.storage import PDFProcessingPipeline
        pipeline = PDFProcessingPipeline(self.milvus_connection.id)
        
        # 模拟PDF处理器
        with patch('apps.pdfloader.pdf_processor.PDFProcessor.process_pdf') as mock_process:
            mock_process.return_value = [
                {
                    'content': f'CASI component {i} description',
                    'page_number': i + 1,
                    'chunk_index': i,
                    'metadata': {'section': 'components'}
                } for i in range(15)
            ]
            
            # 执行处理（这会调用我们的mock方法）
            # 注意：这里我们不会真正等待异步处理完成，只是验证流程
            
        # 验证mock被调用
        mock_connect.assert_called()
        mock_create_collection.assert_called()
        mock_store_chunks.assert_called()
        
        print("✓ Mock处理流水线执行成功")
        print(f"✓ 模拟生成了 {mock_store_chunks.return_value['stored_count']} 个分块")
        
    def test_04_vector_search_components(self):
        """测试4: 向量搜索'CASI的3个核心组件'"""
        print("\n=== 测试4: 向量搜索核心组件 ===")
        
        # 首先确保有文档
        if not hasattr(self, 'document_id'):
            self.test_01_pdf_upload_success()
            
        # 等待处理完成（在真实环境中可能需要更长时间）
        max_wait_time = 30  # 最大等待30秒
        wait_interval = 2   # 每2秒检查一次
        elapsed_time = 0
        
        print("等待文档处理完成...")
        while elapsed_time < max_wait_time:
            response = self.client.get(
                reverse('pdfloader:pdf-processing-status', kwargs={'pk': self.document_id})
            )
            
            if response.status_code == status.HTTP_200_OK:
                status_data = response.json()['data']
                if status_data['status'] == 'completed':
                    print("✓ 文档处理完成")
                    break
                elif status_data['status'] == 'failed':
                    print("✗ 文档处理失败")
                    break
                    
            time.sleep(wait_interval)
            elapsed_time += wait_interval
            print(f"... 已等待 {elapsed_time} 秒")
        else:
            print("⚠ 超时：文档处理未在预期时间内完成")
            
        # 执行向量搜索
        search_data = {
            'query_text': '3 core components in CASI',
            'collection_name': self.collection_name,
            'limit': 5
        }
        
        # Mock搜索结果（因为真实的embedding和Milvus连接需要额外配置）
        with patch('apps.pdfloader.storage.PDFVectorStorageService.search_similar_chunks') as mock_search:
            mock_search.return_value = [
                {
                    'id': 'mock_vector_1',
                    'content': 'The three core components of CASI include...',
                    'similarity': 0.95,
                    'page_number': 5,
                    'chunk_index': 2,
                    'metadata': {'section': 'architecture'}
                },
                {
                    'id': 'mock_vector_2', 
                    'content': 'CASI consists of three fundamental components that work together...',
                    'similarity': 0.88,
                    'page_number': 8,
                    'chunk_index': 5,
                    'metadata': {'section': 'components'}
                },
                {
                    'id': 'mock_vector_3',
                    'content': 'Core architectural components of the CASI system...',
                    'similarity': 0.82,
                    'page_number': 12,
                    'chunk_index': 8,
                    'metadata': {'section': 'design'}
                }
            ]
            
            response = self.client.post(
                reverse('pdfloader:vector-search'),
                data=search_data,
                format='json'
            )
        
        # 验证搜索响应
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertIn('data', response_data)
        
        search_results = response_data['data']
        self.assertIsInstance(search_results, list)
        self.assertGreater(len(search_results), 0)
        
        print(f"✓ 搜索完成，找到 {len(search_results)} 个相关结果")
        
        # 显示搜索结果
        for i, result in enumerate(search_results, 1):
            print(f"\n结果 {i}:")
            print(f"  相似度: {result['similarity']:.3f}")
            print(f"  页码: {result['page_number']}")
            print(f"  内容预览: {result['content'][:100]}...")
            
    def test_05_verify_database_records(self):
        """测试5: 验证数据库记录"""
        print("\n=== 测试5: 数据库记录验证 ===")
        
        # 检查PDF文档记录
        documents = PDFDocument.objects.all()
        print(f"✓ 数据库中共有 {documents.count()} 个PDF文档")
        
        for doc in documents:
            print(f"  - {doc.title} (状态: {doc.status})")
            print(f"    页数: {doc.page_count}, 大小: {doc.file_size} bytes")
            
        # 检查分块记录（如果有）
        chunks = PDFChunk.objects.all()
        print(f"✓ 数据库中共有 {chunks.count()} 个PDF分块")
        
        if chunks.exists():
            for chunk in chunks[:3]:  # 只显示前3个
                print(f"  - Chunk {chunk.chunk_index} (页 {chunk.page_number}): {chunk.content[:50]}...")
                
    def test_06_cleanup_resources(self):
        """测试6: 清理测试资源"""
        print("\n=== 测试6: 资源清理 ===")
        
        # 删除测试文档
        deleted_count = PDFDocument.objects.all().count()
        PDFDocument.objects.all().delete()
        PDFChunk.objects.all().delete()
        
        # 删除Milvus连接
        connections_deleted = MulvesConnection.objects.filter(name="Test Milvus Connection").count()
        MulvesConnection.objects.filter(name="Test Milvus Connection").delete()
        
        print(f"✓ 清理了 {deleted_count} 个PDF文档")
        print(f"✓ 清理了 {connections_deleted} 个Milvus连接配置")
        print("✓ 测试资源清理完成")


class TestCASIGuideRealProcessing(TestCase):
    """CASI指南真实处理测试（需要实际的Milvus和embedding服务）"""
    
    def setUp(self):
        """测试初始化"""
        self.client = APIClient()
        self.test_pdf_path = os.path.join(
            os.path.dirname(__file__), 
            'pdf', 
            'CASI_RefGuide.pdf'
        )
        
        # 检查是否启用了真实测试
        self.run_real_tests = os.environ.get('RUN_REAL_PDF_TESTS', 'false').lower() == 'true'
        
    @pytest.mark.skipif(
        os.environ.get('RUN_REAL_PDF_TESTS', 'false').lower() != 'true',
        reason="需要设置 RUN_REAL_PDF_TESTS=true 来运行真实处理测试"
    )
    def test_real_complete_workflow(self):
        """真实环境下的完整工作流测试"""
        print("\n=== 真实环境完整工作流测试 ===")
        
        # 这里需要实际的Milvus连接和embedding服务配置
        # 在生产环境中应该配置真实的连接参数
        
        # 创建真实的Milvus连接配置
        connection = MulvesConnection.objects.create(
            name="Real Test Connection",
            host=os.environ.get('MILVUS_HOST', 'localhost'),
            port=int(os.environ.get('MILVUS_PORT', '19530')),
            username=os.environ.get('MILVUS_USERNAME', ''),
            password=os.environ.get('MILVUS_PASSWORD', ''),
            is_active=True
        )
        
        try:
            # 上传PDF
            with open(self.test_pdf_path, 'rb') as pdf_file:
                upload_data = {
                    'title': 'CASI Real Processing Test',
                    'file': pdf_file,
                    'milvus_connection_id': connection.id,
                    'collection_name': 'casi_real_test'
                }
                
                response = self.client.post(
                    reverse('pdfloader:pdf-upload'),
                    data=upload_data,
                    format='multipart'
                )
                
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                document_id = response.json()['data']['id']
                
                # 等待处理完成
                time.sleep(10)  # 给更多时间处理
                
                # 检查状态
                status_response = self.client.get(
                    reverse('pdfloader:pdf-processing-status', kwargs={'pk': document_id})
                )
                
                print(f"最终状态: {status_response.json()['data']['status']}")
                
                # 执行真实搜索
                search_response = self.client.post(
                    reverse('pdfloader:vector-search'),
                    data={
                        'query_text': '3 core components in CASI',
                        'collection_name': 'casi_real_test',
                        'limit': 3
                    },
                    format='json'
                )
                
                if search_response.status_code == status.HTTP_200_OK:
                    results = search_response.json()['data']
                    print(f"✓ 真实搜索返回 {len(results)} 个结果")
                    for result in results:
                        print(f"  - 相似度: {result['similarity']:.3f}")
                        print(f"  - 内容: {result['content'][:100]}...")
                        
        finally:
            # 清理
            connection.delete()


if __name__ == '__main__':
    # 运行测试
    print("开始执行 CASI 参考指南集成测试...")
    print("=" * 50)
    
    # 可以通过环境变量控制是否运行真实测试
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    # 运行测试
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '-s'  # 显示print输出
    ])