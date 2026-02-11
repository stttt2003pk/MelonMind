#!/usr/bin/env python
"""
Milvus动态连接演示
展示修改后的连接建立逻辑
"""

import logging
from apps.mulvesdb.models import MulvesConnection
from apps.mulvesdb.connectors import MulvesDBConnector

logger = logging.getLogger(__name__)

def demonstrate_dynamic_connection():
    """演示动态连接建立过程"""
    
    print("=== Milvus动态连接演示 ===\n")
    
    # 使用实际存在的连接ID
    milvus_connection_id = 73  # 根据数据库查询结果
    
    print(f"1. 接收到连接请求，连接ID: {milvus_connection_id}")
    
    try:
        # 步骤1: 根据ID获取连接配置参数
        print("2. 从数据库获取连接配置...")
        connection_config = MulvesConnection.objects.get(
            id=milvus_connection_id, 
            is_active=True
        )
        print(f"   ✓ 获取到配置: {connection_config.name}")
        print(f"   ✓ 主机: {connection_config.host}:{connection_config.port}")
        print(f"   ✓ 用户名: {connection_config.username}")
        print(f"   ✓ 数据库: {connection_config.database}")
        
        # 步骤2: 动态创建连接器实例
        print("3. 动态创建Milvus连接器...")
        milvus_connector = MulvesDBConnector(connection_config)
        print("   ✓ 连接器实例创建成功")
        
        # 步骤3: 建立实际连接
        print("4. 建立Milvus连接...")
        success = milvus_connector.connect_sync()
        if success:
            print("   ✓ Milvus连接建立成功")
        else:
            print("   ✗ 连接建立失败")
            return False
            
        # 步骤4: 执行业务操作（模拟）
        print("5. 执行PDF处理业务逻辑...")
        print("   - 处理PDF文件分块")
        print("   - 生成文本embedding")
        print("   - 存储到Milvus集合")
        # 这里会调用 PDFProcessingPipeline 进行实际处理
        
        # 步骤5: 自动释放连接
        print("6. 自动释放Milvus连接...")
        milvus_connector.disconnect_sync()
        print("   ✓ 连接已安全释放")
        
        print("\n=== 演示完成 ===")
        return True
        
    except MulvesConnection.DoesNotExist:
        print(f"   ✗ 无效的连接ID: {milvus_connection_id}")
        return False
    except Exception as e:
        print(f"   ✗ 连接过程中发生错误: {str(e)}")
        # 确保即使出错也释放连接
        if 'milvus_connector' in locals():
            try:
                milvus_connector.disconnect_sync()
                print("   ✓ 错误处理时连接已释放")
            except:
                pass
        return False

def compare_old_vs_new_approach():
    """对比新旧连接方式"""
    
    print("\n=== 连接方式对比 ===\n")
    
    print("❌ 旧方式（存在问题）:")
    print("   1. 直接获取数据库中的连接对象")
    print("   2. 可能复用已存在的连接")
    print("   3. 连接释放依赖垃圾回收")
    print("   4. 容易造成连接泄露")
    
    print("\n✅ 新方式（改进后）:")
    print("   1. 根据配置ID动态获取连接参数")
    print("   2. 每次请求创建全新的连接实例")
    print("   3. 明确的连接建立和释放流程")
    print("   4. 确保连接资源及时回收")
    print("   5. 更好的错误处理和日志记录")

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 运行演示
    success = demonstrate_dynamic_connection()
    
    # 对比说明
    compare_old_vs_new_approach()
    
    print(f"\n最终结果: {'成功' if success else '失败'}")