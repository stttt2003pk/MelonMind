#!/usr/bin/env python
import os
import sys
import django

# 设置Django环境
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.mulvesdb.models import MulvesConnection
from apps.pdfloader.storage import PDFVectorStorageService

def test_insert_call():
    print("=== 测试 insert_milvus_data_sync 调用 ===")
    
    # 获取Milvus连接
    connection = MulvesConnection.objects.filter(is_active=True).first()
    if not connection:
        print("❌ 没有可用的Milvus连接")
        return
    
    print(f"使用连接: {connection.name}")
    
    # 创建存储服务
    storage_service = PDFVectorStorageService(connection.id)
    
    # 测试数据
    test_data = [{
        'vector_id': 'test_1',
        'content': 'This is a test document for method validation',
        'embedding': [0.1] * 128,
        'page_number': 1,
        'chunk_index': 0,
        'document_id': 999,
        'metadata': {}
    }]
    
    try:
        with storage_service as service:
            print('测试调用 insert_milvus_data_sync...')
            result = service.milvus_connector.insert_milvus_data_sync(
                collection_name='test',
                data=test_data,
                enable_dedup=True,
                document_id=999
            )
            print(f'✅ 调用成功: {result}')
            
    except Exception as e:
        print(f'❌ 调用失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_insert_call()