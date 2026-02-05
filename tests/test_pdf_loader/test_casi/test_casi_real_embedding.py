"""
CASI参考指南真实Embedding服务测试
测试使用真实的embedding API而不是mock服务
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
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.pdfloader.models import PDFDocument, PDFChunk
from apps.mulvesdb.models import MulvesConnection
from apps.pdfloader.embedding import get_embedding_service


@pytest.mark.django_db
class TestCASIRealEmbedding(TestCase):
    """CASI真实Embedding测试"""
    
    def setUp(self):
        """测试初始化"""
        self.client = APIClient()
        self.test_pdf_path = os.path.join(
            os.path.dirname(__file__), 
            'pdf', 
            'CASI_RefGuide.pdf'
        )
        
        # 检查是否应该使用真实embedding服务
        self.use_real_embedding = os.environ.get('USE_MOCK_EMBEDDING', 'true').lower() == 'false'
        
        # 验证API密钥配置
        if self.use_real_embedding:
            self._validate_api_keys()
        
        # 创建Milvus连接配置
        self.milvus_connection = MulvesConnection.objects.create(
            name="CASI Real Embedding Test Connection",
            host=os.environ.get('MILVUS_HOST', 'localhost'),
            port=int(os.environ.get('MILVUS_PORT', '19530')),
            username=os.environ.get('MILVUS_USERNAME', ''),
            password=os.environ.get('MILVUS_PASSWORD', ''),
            is_active=True,
            connection_config={"timeout": 30}
        )
        
        self.collection_name = "casi_real_embedding_test"
        
    def _validate_api_keys(self):
        """验证API密钥配置"""
        qwen_key = os.environ.get('QWEN_API_KEY')
        openai_key = os.environ.get('OPENAI_API_KEY')
        
        if not qwen_key and not openai_key:
            pytest.skip("需要设置QWEN_API_KEY或OPENAI_API_KEY环境变量来运行真实embedding测试")
        
        print("✓ API密钥验证通过")
        if qwen_key:
            print("  使用Qwen API服务")
        if openai_key:
            print("  使用OpenAI API服务")
            
    def test_embedding_service_availability(self):
        """测试embedding服务可用性"""
        print("\n=== 测试embedding服务可用性 ===")
        
        if not self.use_real_embedding:
            pytest.skip("此测试仅在使用真实embedding服务时运行")
            
        # 获取embedding服务
        embedding_service = get_embedding_service(use_mock=False)
        
        # 测试简单的文本embedding
        test_text = "This is a test sentence for embedding."
        
        try:
            result = embedding_service.embed_text(test_text)
            print(f"✓ 成功生成embedding")
            print(f"  文本: {test_text}")
            print(f"  向量维度: {len(result.embedding)}")
            print(f"  模型: {result.model}")
            print(f"  前5维: {result.embedding[:5]}")
            
        except Exception as e:
            pytest.fail(f"Embedding服务调用失败: {e}")
            
    def test_batch_embedding_performance(self):
        """测试批量embedding性能"""
        print("\n=== 测试批量embedding性能 ===")
        
        if not self.use_real_embedding:
            pytest.skip("此测试仅在使用真实embedding服务时运行")
            
        embedding_service = get_embedding_service(use_mock=False)
        
        # 准备测试文本
        test_texts = [
            "The CASI system has three core components.",
            "Component one handles data ingestion and preprocessing.",
            "Component two performs advanced analytics and pattern recognition.",
            "Component three manages visualization and reporting capabilities.",
            "These components work together to provide comprehensive analysis."
        ]
        
        print(f"测试批量处理 {len(test_texts)} 个文本...")
        
        start_time = time.time()
        try:
            results = embedding_service.embed_batch(test_texts)
            end_time = time.time()
            
            processing_time = end_time - start_time
            print(f"✓ 批量embedding完成")
            print(f"  处理时间: {processing_time:.2f} 秒")
            print(f"  平均每个文本: {processing_time/len(test_texts):.3f} 秒")
            print(f"  成功处理: {len(results)} 个文本")
            
            # 验证结果
            for i, result in enumerate(results):
                assert len(result.embedding) > 0, f"第{i+1}个文本的embedding为空"
                assert result.text == test_texts[i], f"第{i+1}个文本内容不匹配"
                
        except Exception as e:
            pytest.fail(f"批量embedding测试失败: {e}")
            
    def test_pdf_processing_with_real_embedding(self):
        """测试使用真实embedding处理PDF"""
        print("\n=== 测试PDF处理与真实embedding ===")
        
        if not self.use_real_embedding:
            pytest.skip("此测试仅在使用真实embedding服务时运行")
            
        # 上传PDF文件
        with open(self.test_pdf_path, 'rb') as pdf_file:
            upload_data = {
                'title': 'CASI Real Embedding Test Document',
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
        assert response.status_code == status.HTTP_201_CREATED
        document_id = response.json()['data']['id']
        print(f"✓ PDF上传成功，文档ID: {document_id}")
        
        # 等待处理完成
        print("等待PDF处理完成...")
        max_wait_time = 60  # 最长等待60秒
        wait_interval = 5
        
        for i in range(max_wait_time // wait_interval):
            status_response = self.client.get(
                reverse('pdfloader:pdf-processing-status', kwargs={'pk': document_id})
            )
            
            if status_response.status_code == status.HTTP_200_OK:
                status_data = status_response.json()['data']
                current_status = status_data['status']
                
                print(f"  状态检查 {i+1}: {current_status}")
                
                if current_status == 'completed':
                    print("✓ PDF处理完成")
                    break
                elif current_status == 'failed':
                    pytest.fail(f"PDF处理失败: {status_data.get('error_message', '未知错误')}")
                    
            time.sleep(wait_interval)
        else:
            pytest.fail("PDF处理超时")
            
        # 验证数据库记录
        document = PDFDocument.objects.get(id=document_id)
        chunks = PDFChunk.objects.filter(document=document)
        
        print(f"✓ 生成了 {chunks.count()} 个文本分块")
        assert chunks.count() > 0, "应该至少生成一个分块"
        
        # 测试向量搜索
        search_data = {
            'query_text': '3 core components in CASI',
            'collection_name': self.collection_name,
            'limit': 3
        }
        
        search_response = self.client.post(
            reverse('pdfloader:vector-search'),
            data=search_data,
            format='json'
        )
        
        assert search_response.status_code == status.HTTP_200_OK
        search_results = search_response.json()['data']
        
        print(f"✓ 向量搜索返回 {len(search_results)} 个结果")
        
        # 验证结果质量
        if search_results:
            best_similarity = search_results[0]['similarity']
            print(f"  最佳匹配相似度: {best_similarity:.3f}")
            assert best_similarity > 0.5, "最佳匹配相似度应该大于0.5"
            
            # 显示最佳结果
            best_result = search_results[0]
            print(f"  最佳匹配内容: {best_result['content'][:100]}...")
            print(f"  页码: {best_result['page_number']}")
            
    def tearDown(self):
        """测试清理"""
        # 删除测试数据
        PDFDocument.objects.filter(title__contains='CASI Real Embedding Test').delete()
        PDFChunk.objects.filter(document__title__contains='CASI Real Embedding Test').delete()
        
        if hasattr(self, 'milvus_connection'):
            self.milvus_connection.delete()


def test_environment_variables():
    """测试环境变量配置"""
    print("\n=== 环境变量检查 ===")
    
    # 检查关键环境变量
    env_vars = {
        'USE_MOCK_EMBEDDING': os.environ.get('USE_MOCK_EMBEDDING', '未设置'),
        'QWEN_API_KEY': '已设置' if os.environ.get('QWEN_API_KEY') else '未设置',
        'OPENAI_API_KEY': '已设置' if os.environ.get('OPENAI_API_KEY') else '未设置',
        'MILVUS_HOST': os.environ.get('MILVUS_HOST', 'localhost'),
        'MILVUS_PORT': os.environ.get('MILVUS_PORT', '19530')
    }
    
    for var, value in env_vars.items():
        print(f"  {var}: {value}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--real-embedding', action='store_true', 
                       help='使用真实embedding服务')
    args = parser.parse_args()
    
    # 设置环境变量
    if args.real_embedding:
        os.environ['USE_MOCK_EMBEDDING'] = 'false'
        print("启用真实embedding服务测试")
    else:
        os.environ['USE_MOCK_EMBEDDING'] = 'true'
        print("使用mock embedding服务测试")
    
    # 运行测试
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '-s'
    ])