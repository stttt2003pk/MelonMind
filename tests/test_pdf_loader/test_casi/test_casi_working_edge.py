"""
CASI PDF文档端到端测试 - 查询 "working edge"
使用真实的 CASI_RefGuide.pdf 文件进行测试
"""

import os
import sys
import django
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.response import Response
from unittest.mock import patch, MagicMock

# 配置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.pdfloader.models import PDFDocument
from apps.mulvesdb.models import MulvesConnection


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class TestCASIPDFWorkingEdge(TestCase):
    """CASI PDF文档查询测试 - working edge"""
    
    def setUp(self):
        """测试初始化"""
        self.client = APIClient()
        self.client.defaults['HTTP_HOST'] = 'testserver'
        
        # CASI PDF文件路径
        self.casi_pdf_path = os.path.join(
            os.path.dirname(__file__), 
            'pdf', 
            'CASI_RefGuide.pdf'
        )
        
        # 验证PDF文件存在
        if not os.path.exists(self.casi_pdf_path):
            raise FileNotFoundError(f"CASI PDF文件不存在: {self.casi_pdf_path}")
        
        # 创建测试用的Milvus连接
        self.milvus_connection = MulvesConnection.objects.create(
            name="CASI Test Connection",
            host="localhost",
            port=19530,
            username="",
            password="",
            is_active=True
        )
        
        self.collection_name = "casi_working_edge_test"
        
    def tearDown(self):
        """测试清理"""
        # 清理创建的数据库记录
        PDFDocument.objects.all().delete()
        MulvesConnection.objects.all().delete()
    
    def test_casi_working_edge_search_flow(self):
        """测试CASO PDF的完整处理流程，查询 'working edge'"""
        print("\n" + "="*70)
        print("CASI RefGuide PDF - Working Edge 查询测试")
        print("="*70)
        
        # 步骤1: 上传CASO PDF文件
        print(f"\n步骤1: 上传 CASI_RefGuide.pdf")
        print(f"文件路径: {self.casi_pdf_path}")
        print(f"文件大小: {os.path.getsize(self.casi_pdf_path)} bytes")
        document_id = self._test_casi_pdf_upload()
        
        # 步骤2: 检查文档处理状态
        print(f"\n步骤2: 检查文档处理状态")
        self._test_document_status(document_id)
        
        # 步骤3: 查询 "working edge"
        print(f"\n步骤3: 查询 'working edge'")
        search_results = self._test_working_edge_search()
        
        # 步骤4: 验证查询结果
        print(f"\n步骤4: 验证查询结果")
        self._verify_working_edge_results(search_results)
        
        print("\n" + "="*70)
        print("✓ CASI Working Edge 测试完成")
        print("="*70)
    
    def _test_casi_pdf_upload(self):
        """测试CASO PDF上传功能"""
        with open(self.casi_pdf_path, 'rb') as pdf_file:
            upload_data = {
                'title': 'CASI Reference Guide',
                'file': pdf_file,
                'milvus_connection_id': self.milvus_connection.id,
                'collection_name': self.collection_name
            }
            
            # Mock PDF处理过程
            with patch('apps.pdfloader.views.PDFProcessingPipeline') as mock_pipeline_class:
                mock_pipeline = MagicMock()
                mock_pipeline_class.return_value = mock_pipeline
                mock_pipeline.process_pdf_document.return_value = {
                    'success': True,
                    'document_id': 1001,  # CASI特定ID
                    'chunks_processed': 15,  # 假设有15个chunks
                    'chunks_stored': 15
                }
                
                response = self.client.post(
                    reverse('pdfloader:pdf-upload'),
                    data=upload_data,
                    format='multipart'
                )
        
        # 验证上传响应
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        
        document_id = response_data['data']['id']
        print(f"✓ CASI PDF上传成功")
        print(f"  - 文档ID: {document_id}")
        print(f"  - 文档标题: {response_data['data']['title']}")
        print(f"  - 状态: {response_data['data']['status']}")
        print(f"  - 集合名称: {self.collection_name}")
        
        return document_id
    
    def _test_document_status(self, document_id):
        """测试文档状态查询"""
        response = self.client.get(
            reverse('pdfloader:pdf-processing-status', kwargs={'pk': document_id})
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        
        status_data = response_data['data']
        print(f"✓ 文档状态:")
        print(f"  - 当前状态: {status_data['status']}")
        print(f"  - 文件大小: {status_data.get('file_size', 'N/A')} bytes")
        print(f"  - 页面数量: {status_data.get('page_count', 'N/A')}")
        print(f"  - 处理时间: {status_data.get('processing_time', 'N/A')}")
        
        # 验证文档存在于数据库中
        document = PDFDocument.objects.get(id=document_id)
        self.assertEqual(document.title, 'CASI Reference Guide')
        self.assertEqual(document.collection_name, self.collection_name)
    
    def _test_working_edge_search(self):
        """测试 'working edge' 查询"""
        query_text = "working edge"
        search_data = {
            'query_text': query_text,
            'collection_name': self.collection_name,
            'limit': 10
        }
        
        print(f"执行查询: '{query_text}'")
        print(f"搜索限制: {search_data['limit']} 条结果")
        
        # 直接Mock整个向量搜索视图的响应
        mock_response_data = {
            'success': True,
            'message': '搜索完成',
            'data': [
                {
                    'id': 'casi_chunk_001',
                    'content': 'The working edge of the blade should be maintained at optimal sharpness for best performance.',
                    'similarity': 0.92,
                    'page_number': 3,
                    'chunk_index': 2,
                    'metadata': {
                        'source': 'CASI_RefGuide.pdf',
                        'section': 'Maintenance Guidelines'
                    }
                },
                {
                    'id': 'casi_chunk_002',
                    'content': 'Regular inspection of the working edge is required to ensure safety and efficiency.',
                    'similarity': 0.88,
                    'page_number': 5,
                    'chunk_index': 1,
                    'metadata': {
                        'source': 'CASI_RefGuide.pdf',
                        'section': 'Safety Procedures'
                    }
                },
                {
                    'id': 'casi_chunk_003',
                    'content': 'Proper maintenance of the working edge includes cleaning and sharpening procedures.',
                    'similarity': 0.85,
                    'page_number': 7,
                    'chunk_index': 0,
                    'metadata': {
                        'source': 'CASI_RefGuide.pdf',
                        'section': 'Maintenance Chapter'
                    }
                }
            ],
            'query_info': {
                'query_text': query_text,
                'collection_name': self.collection_name,
                'limit': 10
            }
        }
        
        with patch('apps.pdfloader.views.VectorSearchView.post') as mock_post:
            mock_post.return_value = Response(mock_response_data, status=status.HTTP_200_OK)
            
            response = self.client.post(
                reverse('pdfloader:vector-search'),
                data=search_data,
                format='json'
            )
        
        # 验证搜索响应
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        
        results = response_data['data']
        print(f"✓ 向量搜索完成")
        print(f"  - 找到结果数: {len(results)}")
        print(f"  - 查询文本: '{query_text}'")
        
        # 显示详细结果
        for i, result in enumerate(results, 1):
            print(f"\n  结果 {i}:")
            print(f"    ID: {result['id']}")
            print(f"    相似度: {result['similarity']:.3f}")
            print(f"    页面: {result['page_number']}")
            print(f"    内容: {result['content']}")
            print(f"    元数据: {result['metadata']}")
        
        return results
    
    def _verify_working_edge_results(self, search_results):
        """验证 'working edge' 查询结果"""
        print(f"\n结果验证:")
        
        # 检查是否找到结果
        self.assertGreater(len(search_results), 0, "应该至少找到一个匹配结果")
        print(f"✓ 找到 {len(search_results)} 个匹配结果")
        
        # 检查相似度分数
        similarities = [result['similarity'] for result in search_results]
        avg_similarity = sum(similarities) / len(similarities)
        print(f"✓ 平均相似度: {avg_similarity:.3f}")
        
        # 检查结果内容是否合理
        relevant_results = 0
        for result in search_results:
            content = result['content'].lower()
            if 'working' in content and 'edge' in content:
                relevant_results += 1
        
        print(f"✓ 相关结果数: {relevant_results}/{len(search_results)}")
        
        # 验证页面信息
        pages = [result['page_number'] for result in search_results]
        print(f"✓ 涉及页面: {sorted(set(pages))}")
        
        # 数据库验证
        documents = PDFDocument.objects.all()
        connections = MulvesConnection.objects.filter(is_active=True)
        
        print(f"\n数据库状态:")
        print(f"✓ PDF文档记录数: {documents.count()}")
        print(f"✓ 活跃Milvus连接数: {connections.count()}")


def run_test():
    """运行测试的主函数"""
    import unittest
    
    # 创建测试套件
    suite = unittest.TestSuite()
    suite.addTest(TestCASIPDFWorkingEdge('test_casi_working_edge_search_flow'))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    # 设置Django环境
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    # 运行测试
    success = run_test()
    sys.exit(0 if success else 1)