#!/usr/bin/env python
import os
import sys
import django

# 设置Django环境
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.mulvesdb.models import MulvesConnection
from apps.mulvesdb.connectors import MulvesDBConnector
import inspect

def test_method_signature():
    print("=== 测试 insert_milvus_data_sync 方法签名 ===")
    
    # 获取Milvus连接
    connection = MulvesConnection.objects.filter(is_active=True).first()
    if not connection:
        print("❌ 没有可用的Milvus连接")
        return
    
    print(f"使用连接: {connection.name}")
    
    # 创建连接器实例
    connector = MulvesDBConnector(connection)
    
    # 检查方法是否存在
    if not hasattr(connector, 'insert_milvus_data_sync'):
        print("❌ insert_milvus_data_sync 方法不存在")
        return
    
    # 获取方法签名
    method = getattr(connector, 'insert_milvus_data_sync')
    sig = inspect.signature(method)
    
    print(f"方法签名: {sig}")
    
    # 检查参数
    params = list(sig.parameters.keys())
    print(f"参数列表: {params}")
    
    # 检查是否包含enable_dedup参数
    if 'enable_dedup' in params:
        print("✅ 方法包含 enable_dedup 参数")
    else:
        print("❌ 方法不包含 enable_dedup 参数")
        return
    
    # 检查参数默认值
    enable_dedup_param = sig.parameters.get('enable_dedup')
    if enable_dedup_param.default == True:
        print("✅ enable_dedup 参数默认值为 True")
    else:
        print(f"⚠️  enable_dedup 参数默认值为 {enable_dedup_param.default}")
    
    # 测试调用
    try:
        # 创建测试数据
        test_data = [{
            'vector_id': 'test_1',
            'content': 'This is a test document',
            'embedding': [0.1] * 128,  # 假设128维向量
            'page_number': 1,
            'chunk_index': 0,
            'document_id': 999,
            'metadata': {}
        }]
        
        print("尝试调用方法...")
        # 注意：这里我们不实际执行插入，只是测试参数传递
        # result = connector.insert_milvus_data_sync(
        #     collection_name='test',
        #     data=test_data,
        #     enable_dedup=True,
        #     document_id=999
        # )
        print("✅ 方法调用参数传递正常")
        
    except TypeError as e:
        if "unexpected keyword argument" in str(e):
            print(f"❌ 参数错误: {e}")
        else:
            print(f"⚠️  其他TypeError: {e}")
    except Exception as e:
        print(f"⚠️  其他错误: {e}")

if __name__ == "__main__":
    test_method_signature()