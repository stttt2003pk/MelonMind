"""
简化的CASi端到端测试 - 从上传到查询的核心流程
"""

import os
import sys
import time
import django
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

# 配置Django设置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from apps.pdfloader.models import PDFDocument
from apps.mulvesdb.models import MulvesConnection
from unittest.mock import patch


class TestCASISimpleE2EFlow(TestCase):
    """CASi简单端到端流程测试"""
    
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
        
        # 创建Milvus连接配置
        self.milvus_connection = MulvesConnection.objects.create(
            name="CASI Simple E2E Test",
            host="localhost",
            port=19530,
            username="",
            password="",
            is_active=True
        )
        
        self.collection_name = "casi_simple_e2e_test"
        
    def test_upload_and_basic_search_flow(self):
        """测试上传和基础搜索流程"""
        print("\n" + "="*60)
        print("CASi端到端测试 - 上传到查询流程")
        print("="*60)
        
        # 步骤1: 上传PDF文件
        print("\n步骤1: 上传PDF文件")
        document_id = self._upload_pdf()
        
        # 步骤2: 检查初始状态
        print("\n步骤2: 检查文档状态")
        self._check_document_status(document_id)
        
        # 步骤3: 执行向量搜索（使用mock）
        print("\n步骤3: 执行向量搜索")
        self._perform_mock_search()
        
        # 步骤4: 验证结果
        print("\n步骤4: 验证测试结果")
        self._verify_test_results()
        
        print("\n" + "="*60)
        print("✓ CASi端到端测试完成")
        print("="*60)
        
    def _upload_pdf(self):
        """上传PDF文件"""
        with open(self.test_pdf_path, 'rb') as pdf_file:
            upload_data = {
                'title': 'CASi Reference Guide E2E Test',
                'file': pdf_file,
                'milvus_connection_id': self.milvus_connection.id,
                'collection_name': self.collection_name
            }
            
            response = self.client.post(
                reverse('pdfloader:pdf-upload'),
                data=upload_data,
                format='multipart'
            )
            
        # 验证上传成功
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        
        document_id = response_data['data']['id']
        print(f"✓ PDF上传成功")
        print(f"  - 文档ID: {document_id}")
        print(f"  - 文档标题: {response_data['data']['title']}")
        print(f"  - 集合名称: {response_data['data']['collection_name']}")
        print(f"  - 当前状态: {response_data['data']['status']}")
        
        return document_id
        
    def _check_document_status(self, document_id):
        """检查文档状态"""
        response = self.client.get(
            reverse('pdfloader:pdf-processing-status', kwargs={'pk': document_id})
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        
        status_data = response_data['data']
        print(f"✓ 文档状态详情:")
        print(f"  - 状态: {status_data['status']}")
        print(f"  - 文件大小: {status_data.get('file_size', 'N/A')} bytes")
        if 'page_count' in status_data:
            print(f"  - 页数: {status_data['page_count']}")
            
    def _perform_mock_search(self):
        """执行mock向量搜索"""
        search_queries = [
            '3 core components in CASi',
            'CASi architecture overview',
            'main features of CASi system'
        ]
        
        print(f"执行 {len(search_queries)} 个搜索查询:")
        
        # Mock搜索结果
        mock_results = [
            {
                'id': 'vector_001',
                'content': 'The CASi system comprises three core architectural components that form the foundation of modern document processing...',
                'similarity': 0.92,
                'page_number': 3,
                'chunk_index': 1,
                'metadata': {'section': 'architecture', 'component': 'core'}
            },
            {
                'id': 'vector_002', 
                'content': 'Three fundamental components define the CASi framework: data processing engine, analysis module, and visualization interface...',
                'similarity': 0.87,
                'page_number': 7,
                'chunk_index': 3,
                'metadata': {'section': 'components', 'component': 'framework'}
            },
            {
                'id': 'vector_003',
                'content': 'The essential components of CASi include the core processing module, interactive user interface, and storage management subsystem...',
                'similarity': 0.81,
                'page_number': 12,
                'chunk_index': 6,
                'metadata': {'section': 'system', 'component': 'essential'}
            }
        ]
        
        with patch('apps.pdfloader.storage.PDFVectorStorageService.search_similar_chunks', 
                   return_value=mock_results):
            
            for i, query_text in enumerate(search_queries, 1):
                print(f"\n查询 {i}: '{query_text}'")
                
                search_data = {
                    'query_text': query_text,
                    'collection_name': self.collection_name,
                    'limit': 3
                }
                
                response = self.client.post(
                    reverse('pdfloader:vector-search'),
                    data=search_data,
                    format='json'
                )
                
                if response.status_code == status.HTTP_200_OK:
                    results = response.json()['data']
                    print(f"  ✓ 找到 {len(results)} 个相关结果")
                    
                    for j, result in enumerate(results, 1):
                        print(f"    结果 {j}:")
                        print(f"      相似度: {result['similarity']:.3f}")
                        print(f"      页码: {result['page_number']}")
                        print(f"      内容预览: {result['content'][:100]}...")
                else:
                    print(f"  ✗ 搜索失败: {response.status_code}")
                    if response.content:
                        print(f"    错误详情: {response.content.decode()}")
                        
    def _verify_test_results(self):
        """验证测试结果"""
        # 检查数据库记录
        documents = PDFDocument.objects.all()
        print(f"\n数据库验证:")
        print(f"✓ 创建了 {documents.count()} 个PDF文档记录")
        
        for doc in documents:
            print(f"  - {doc.title}")
            print(f"    状态: {doc.status}")
            print(f"    集合: {doc.collection_name}")
            print(f"    文件大小: {doc.file_size} bytes")
            
        # 验证Milvus连接
        connections = MulvesConnection.objects.filter(is_active=True)
        print(f"✓ 活跃的Milvus连接数: {connections.count()}")
        
        # 验证API端点可达性
        endpoints = [
            ('pdfloader:pdf-document-list', 'PDF文档列表'),
            ('pdfloader:pdf-upload', 'PDF上传'),
            ('pdfloader:vector-search', '向量搜索')
        ]
        
        print(f"\nAPI端点验证:")
        for url_name, description in endpoints:
            try:
                url = reverse(url_name)
                print(f"✓ {description}: {url}")
            except Exception as e:
                print(f"✗ {description}: {str(e)}")


if __name__ == '__main__':
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    import django
    django.setup()
    
    import unittest
    unittest.main()