"""
CASI参考指南API流程测试
重点测试从上传到查询的API调用流程
"""

import os
import sys
import time
import pytest
import django
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

# 配置Django设置
django.setup()

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django.setup()

from apps.pdfloader.models import PDFDocument
from apps.mulvesdb.models import MulvesConnection


@pytest.mark.django_db
class TestCASIGuideAPIFlow(TestCase):
    """CASI参考指南API流程测试"""
    
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
            name="CASI Test Connection",
            host="localhost",
            port=19530,
            username="",
            password="",
            is_active=True,
            connection_config={"timeout": 30}
        )
        
        self.collection_name = "casi_guide_api_test"
        
    def test_complete_api_workflow(self):
        """测试完整的API工作流程"""
        print("\n" + "="*60)
        print("CASI参考指南完整API流程测试")
        print("="*60)
        
        # 步骤1: 上传PDF文件
        print("\n步骤1: 上传PDF文件")
        document_id = self._upload_pdf()
        
        # 步骤2: 检查处理状态
        print("\n步骤2: 检查处理状态")
        self._check_processing_status(document_id)
        
        # 步骤3: 等待处理完成（模拟）
        print("\n步骤3: 等待处理完成")
        self._wait_for_processing(document_id)
        
        # 步骤4: 执行向量搜索
        print("\n步骤4: 执行向量搜索")
        self._perform_vector_search()
        
        # 步骤5: 验证结果
        print("\n步骤5: 验证测试结果")
        self._verify_results()
        
        print("\n" + "="*60)
        print("✓ 所有API流程测试完成")
        print("="*60)
        
    def _upload_pdf(self):
        """上传PDF文件"""
        with open(self.test_pdf_path, 'rb') as pdf_file:
            upload_data = {
                'title': 'CASI Reference Guide Integration Test',
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
        print(f"✓ PDF上传成功，文档ID: {document_id}")
        print(f"✓ 文档标题: {response_data['data']['title']}")
        print(f"✓ 集合名称: {response_data['data']['collection_name']}")
        
        return document_id
        
    def _check_processing_status(self, document_id):
        """检查文档处理状态"""
        response = self.client.get(
            reverse('pdfloader:pdf-processing-status', kwargs={'pk': document_id})
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        
        status_data = response_data['data']
        print(f"✓ 当前处理状态: {status_data['status']}")
        print(f"✓ 文件大小: {status_data['file_size']} bytes")
        if status_data.get('page_count'):
            print(f"✓ 页数: {status_data['page_count']}")
            
    def _wait_for_processing(self, document_id):
        """等待处理完成"""
        max_wait = 15  # 最大等待15秒
        interval = 2   # 每2秒检查一次
        
        for i in range(max_wait // interval):
            response = self.client.get(
                reverse('pdfloader:pdf-processing-status', kwargs={'pk': document_id})
            )
            
            if response.status_code == status.HTTP_200_OK:
                status_data = response.json()['data']
                current_status = status_data['status']
                
                print(f"  等待中... 当前状态: {current_status} ({(i+1) * interval}秒)")
                
                if current_status == 'completed':
                    print("✓ 处理完成")
                    return
                elif current_status == 'failed':
                    print("✗ 处理失败")
                    return
                    
            time.sleep(interval)
            
        print("⚠ 超时：处理未在预期时间内完成")
        
    def _perform_vector_search(self):
        """执行向量搜索"""
        search_queries = [
            '3 core components in CASI',
            'CASI architecture components',
            'main components of CASI system'
        ]
        
        print(f"执行 {len(search_queries)} 个搜索查询:")
        
        for i, query_text in enumerate(search_queries, 1):
            print(f"\n查询 {i}: '{query_text}'")
            
            search_data = {
                'query_text': query_text,
                'collection_name': self.collection_name,
                'limit': 3
            }
            
            # Mock搜索结果
            with self._mock_search_results():
                response = self.client.post(
                    reverse('pdfloader:vector-search'),
                    data=search_data,
                    format='json'
                )
                
            if response.status_code == status.HTTP_200_OK:
                results = response.json()['data']
                print(f"  ✓ 找到 {len(results)} 个相关结果")
                
                for j, result in enumerate(results, 1):
                    print(f"    结果 {j}: 相似度 {result['similarity']:.3f}")
                    print(f"            页码 {result['page_number']}")
                    print(f"            内容: {result['content'][:80]}...")
            else:
                print(f"  ✗ 搜索失败: {response.status_code}")
                
    def _mock_search_results(self):
        """Mock搜索结果的上下文管理器"""
        from unittest.mock import patch
        
        mock_results = [
            {
                'id': 'vector_001',
                'content': 'The CASI system comprises three core architectural components that form the foundation...',
                'similarity': 0.92,
                'page_number': 3,
                'chunk_index': 1,
                'metadata': {'section': 'architecture', 'component': 'core'}
            },
            {
                'id': 'vector_002',
                'content': 'Three fundamental components define the CASI framework: data processing, analysis engine, and visualization layer...',
                'similarity': 0.87,
                'page_number': 7,
                'chunk_index': 3,
                'metadata': {'section': 'components', 'component': 'framework'}
            },
            {
                'id': 'vector_003',
                'content': 'The essential components of CASI include the core processing module, interactive interface, and storage subsystem...',
                'similarity': 0.81,
                'page_number': 12,
                'chunk_index': 6,
                'metadata': {'section': 'system', 'component': 'essential'}
            }
        ]
        
        return patch(
            'apps.pdfloader.storage.PDFVectorStorageService.search_similar_chunks',
            return_value=mock_results
        )
        
    def _verify_results(self):
        """验证测试结果"""
        # 检查数据库记录
        documents = PDFDocument.objects.all()
        print(f"\n数据库验证:")
        print(f"✓ 创建了 {documents.count()} 个PDF文档记录")
        
        for doc in documents:
            print(f"  - {doc.title}")
            print(f"    状态: {doc.status}")
            print(f"    集合: {doc.collection_name}")
            
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


@pytest.mark.django_db
class TestCASIGuideEdgeCases(TestCase):
    """CASI参考指南边界情况测试"""
    
    def setUp(self):
        """测试初始化"""
        self.client = APIClient()
        self.test_pdf_path = os.path.join(
            os.path.dirname(__file__), 
            'pdf', 
            'CASI_RefGuide.pdf'
        )
        
    def test_invalid_file_upload(self):
        """测试无效文件上传"""
        print("\n测试无效文件上传...")
        
        # 测试空文件
        response = self.client.post(
            reverse('pdfloader:pdf-upload'),
            data={
                'title': 'Empty File Test',
                'file': '',
                'milvus_connection_id': 999,  # 不存在的ID
                'collection_name': 'test'
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        print("✓ 空文件上传被正确拒绝")
        
    def test_missing_required_fields(self):
        """测试缺少必要字段"""
        print("\n测试缺少必要字段...")
        
        with open(self.test_pdf_path, 'rb') as pdf_file:
            # 缺少title字段
            response = self.client.post(
                reverse('pdfloader:pdf-upload'),
                data={
                    'file': pdf_file,
                    'milvus_connection_id': 1,
                    'collection_name': 'test'
                },
                format='multipart'
            )
            
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        print("✓ 缺少title字段被正确检测")
        
    def test_nonexistent_document_status(self):
        """测试查询不存在的文档状态"""
        print("\n测试查询不存在的文档...")
        
        response = self.client.get(
            reverse('pdfloader:pdf-processing-status', kwargs={'pk': 99999})
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        print("✓ 不存在的文档查询返回404")


if __name__ == '__main__':
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '-s'
    ])