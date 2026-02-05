"""
MulvesDB使用示例
演示如何使用调整后的连接器连接本地Milvus环境
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 等待Django完全加载后再导入模型
import django
django.setup()

from apps.mulvesdb.models import MulvesConnection
from apps.mulvesdb.connectors import MulvesDBConnector, MulvesDBService
from apps.mulvesdb.local_config import MilvusLocalConfig


async def example_local_milvus_usage():
    """本地Milvus使用示例"""
    
    print("🚀 MulvesDB本地Milvus使用示例")
    print("=" * 50)
    
    # 1. 获取本地配置
    local_config = MilvusLocalConfig.create_test_connection_config()
    print(f"📊 本地配置: {local_config}")
    
    # 2. 创建连接对象
    connection = MulvesConnection(**local_config)
    connector = MulvesDBConnector(connection)
    
    try:
        # 3. 连接数据库
        print("\n🔌 正在连接数据库...")
        await connector.connect()
        print("✅ 连接成功!")
        
        # 4. 执行基本查询
        print("\n🔍 执行基本查询...")
        try:
            # 获取数据库版本（如果支持）
            version_result = await connector.execute_query("SELECT version()")
            print(f"📦 数据库版本: {version_result}")
        except Exception as e:
            print(f"⚠️  版本查询失败: {e}")
        
        # 5. 获取集合信息
        print("\n📚 获取集合信息...")
        try:
            collections = await connector.get_milvus_collections_info()
            print(f"📁 找到 {len(collections)} 个集合")
            for collection in collections[:5]:  # 显示前5个
                print(f"   • {collection}")
        except Exception as e:
            print(f"⚠️  获取集合信息失败: {e}")
        
        # 6. 向量搜索示例（如果有测试数据）
        print("\n🎯 向量搜索示例...")
        try:
            # 示例向量搜索（需要实际的集合和字段名）
            sample_vector = [0.1] * 128  # 128维向量示例
            search_results = await connector.execute_milvus_vector_search(
                collection_name="test_collection",
                vector_field="embedding",
                query_vector=sample_vector,
                limit=5
            )
            print(f"🔍 搜索结果: {len(search_results)} 条记录")
        except Exception as e:
            print(f"⚠️  向量搜索失败: {e}")
            print("💡 提示: 可能需要先创建测试集合和数据")
            
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        
    finally:
        # 7. 断开连接
        print("\n🔌 断开连接...")
        await connector.disconnect()
        print("✅ 连接已断开")


async def example_connection_management():
    """连接管理示例"""
    
    print("\n🔧 连接管理示例")
    print("=" * 30)
    
    # 使用上下文管理器自动处理连接
    local_config = MilvusLocalConfig.create_test_connection_config()
    connection = MulvesConnection(**local_config)
    
    try:
        async with MulvesDBConnector(connection) as connector:
            print("✅ 使用上下文管理器连接成功")
            
            # 执行一些操作
            try:
                result = await connector.execute_query("SELECT 1")
                print(f"📊 查询结果: {result}")
            except Exception as e:
                print(f"⚠️  查询执行失败: {e}")
                
    except Exception as e:
        print(f"❌ 连接管理示例失败: {e}")


if __name__ == "__main__":
    print("开始执行MulvesDB示例...")
    
    # 运行示例
    asyncio.run(example_local_milvus_usage())
    asyncio.run(example_connection_management())
    
    print("\n🎉 示例执行完成!")