#!/usr/bin/env python3
"""
本地Milvus测试脚本
用于测试与本地部署的Milvus数据库的连接和基本操作
"""

import os
import sys
import asyncio
import django
from pathlib import Path

# 添加项目路径到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.mulvesdb.models import MulvesConnection
from apps.mulvesdb.connectors import MulvesDBService, MulvesDBConnector
from apps.mulvesdb.local_config import MilvusLocalConfig, MilvusEnvironmentChecker


async def test_local_milvus_connection():
    """测试本地Milvus连接"""
    print("🔍 开始测试本地Milvus连接...")
    
    # 1. 检查环境
    print("\n📋 环境检查:")
    checker = MilvusEnvironmentChecker()
    docker_status = checker.check_docker_services()
    port_available = checker.check_port_availability()
    
    print(f"  Docker服务状态: {docker_status}")
    print(f"  Milvus端口可用: {port_available}")
    
    if not port_available:
        print("❌ Milvus端口不可用，请检查Docker容器是否正常运行")
        return False
    
    # 2. 获取本地配置
    print("\n⚙️  获取本地配置:")
    local_config = MilvusLocalConfig.get_local_config()
    for key, value in local_config.items():
        print(f"  {key}: {value}")
    
    # 3. 测试连接
    print("\n🔌 测试数据库连接:")
    test_result = await MulvesDBService.test_connection(local_config)
    
    if test_result['success']:
        print("✅ 连接测试成功!")
        print(f"  测试结果: {test_result.get('test_result', 'N/A')}")
    else:
        print("❌ 连接测试失败!")
        print(f"  错误信息: {test_result['message']}")
        return False
    
    # 4. 创建连接配置记录（如果不存在）
    print("\n💾 保存连接配置:")
    try:
        connection, created = await MulvesConnection.objects.aget_or_create(
            name=local_config['name'],
            defaults=MilvusLocalConfig.create_test_connection_config()
        )
        
        if created:
            print(f"  ✅ 创建新的连接配置: {connection.name}")
        else:
            print(f"  ℹ️  使用现有连接配置: {connection.name}")
            
    except Exception as e:
        print(f"  ⚠️  保存连接配置时出错: {e}")
    
    return True


async def test_milvus_operations():
    """测试Milvus基本操作"""
    print("\n🧪 测试Milvus基本操作:")
    
    try:
        # 获取本地连接配置
        local_config = MilvusLocalConfig.create_test_connection_config()
        connection = MulvesConnection(**local_config)
        
        # 建立连接
        async with MulvesDBConnector(connection) as connector:
            # 测试获取集合信息
            print("  🔍 获取集合信息...")
            try:
                collections = await connector.get_milvus_collections_info()
                print(f"    找到 {len(collections)} 个集合")
                for collection in collections[:3]:  # 显示前3个
                    print(f"    - {collection}")
            except Exception as e:
                print(f"    获取集合信息失败: {e}")
            
            # 测试简单查询
            print("  📊 执行简单查询...")
            try:
                result = await connector.execute_query("SELECT version()")
                print(f"    数据库版本: {result}")
            except Exception as e:
                print(f"    查询执行失败: {e}")
                
    except Exception as e:
        print(f"  ❌ 操作测试失败: {e}")


def show_help():
    """显示帮助信息"""
    help_text = """
🚀 本地Milvus测试工具使用说明

命令选项:
  test-connect    测试数据库连接
  test-ops        测试基本操作
  check-env       检查环境状态
  help           显示此帮助信息

环境变量配置:
  MILVUS_HOST         Milvus主机地址 (默认: localhost)
  MILVUS_PORT         Milvus端口 (默认: 19530)
  MILVUS_DATABASE     数据库名称 (默认: default)
  MILVUS_USERNAME     用户名 (可选)
  MILVUS_PASSWORD     密码 (可选)
  MILVUS_TIMEOUT      连接超时时间 (默认: 30)

使用示例:
  python test_local_milvus.py test-connect
  python test_local_milvus.py test-ops
  MILVUS_HOST=192.168.1.100 python test_local_milvus.py test-connect
    """
    print(help_text)


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == 'test-connect':
            success = await test_local_milvus_connection()
            sys.exit(0 if success else 1)
        elif command == 'test-ops':
            await test_milvus_operations()
        elif command == 'check-env':
            print("🔧 环境状态检查:")
            checker = MilvusEnvironmentChecker()
            print(f"  Docker服务: {checker.check_docker_services()}")
            print(f"  端口可用性: {checker.check_port_availability()}")
            print(f"  本地配置: {MilvusLocalConfig.get_local_config()}")
        elif command == 'help':
            show_help()
        else:
            print(f"❌ 未知命令: {command}")
            show_help()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())