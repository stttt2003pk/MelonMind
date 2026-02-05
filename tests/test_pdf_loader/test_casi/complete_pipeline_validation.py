#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整的PDF处理管道验证脚本
包括Milvus集合创建、embedding服务配置和完整处理流程测试
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def test_milvus_collection_logic():
    """测试Milvus集合创建逻辑"""
    print("🔍 测试Milvus集合创建逻辑...")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        import django
        django.setup()
        
        from apps.mulvesdb.models import MulvesConnection
        from apps.mulvesdb.connectors import MulvesDBConnector
        
        # 获取连接配置
        connection = MulvesConnection.objects.get(id=1, is_active=True)
        print(f"✅ 连接配置: {connection.host}:{connection.port}")
        
        connector = MulvesDBConnector(connection)
        
        async def test_operations():
            try:
                # 连接Milvus
                await connector.connect()
                print("✅ 成功连接到Milvus")
                
                # 检查现有集合
                collections = connector._milvus_client.list_collections()
                print(f"📚 现有集合: {collections}")
                
                # 测试创建集合
                test_collection = 'validation_test_collection'
                
                # 定义正确的schema
                schema = {
                    'fields': [
                        {
                            'name': 'id',
                            'type': 'INT64',
                            'is_primary': True,
                            'auto_id': True
                        },
                        {
                            'name': 'vector_id',
                            'type': 'VARCHAR',
                            'max_length': 100
                        },
                        {
                            'name': 'content',
                            'type': 'VARCHAR',
                            'max_length': 65535
                        },
                        {
                            'name': 'embedding',
                            'type': 'FLOAT_VECTOR',
                            'dim': 128  # Qwen embedding维度
                        },
                        {
                            'name': 'page_number',
                            'type': 'INT64'
                        },
                        {
                            'name': 'chunk_index',
                            'type': 'INT64'
                        },
                        {
                            'name': 'document_id',
                            'type': 'INT64'
                        },
                        {
                            'name': 'metadata',
                            'type': 'JSON'
                        }
                    ],
                    'description': 'PDF处理验证测试集合'
                }
                
                # 创建集合
                connector._milvus_client.create_collection(
                    collection_name=test_collection,
                    schema=schema
                )
                print(f"✅ 成功创建集合: {test_collection}")
                
                # 验证创建
                new_collections = connector._milvus_client.list_collections()
                if test_collection in new_collections:
                    print("✅ 集合创建验证通过")
                    
                    # 清理测试集合
                    connector._milvus_client.drop_collection(test_collection)
                    print(f"🗑️  清理测试集合: {test_collection}")
                
                await connector.disconnect()
                return True
                
            except Exception as e:
                print(f"❌ 集合操作失败: {str(e)}")
                return False
        
        result = asyncio.run(test_operations())
        return result
        
    except Exception as e:
        print(f"❌ 测试准备失败: {str(e)}")
        return False

def test_embedding_service_config():
    """验证embedding服务配置"""
    print("\n🔍 验证embedding服务配置...")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        import django
        django.setup()
        
        from apps.pdfloader.embedding import get_embedding_service
        
        # 获取embedding服务
        embedding_service = get_embedding_service()
        print(f"✅ Embedding服务类型: {type(embedding_service).__name__}")
        
        # 测试embedding生成
        test_texts = [
            "This is a test document for PDF processing.",
            "CASI reference guide contains important information.",
            "Machine learning and artificial intelligence applications."
        ]
        
        print("🧪 测试embedding生成...")
        embeddings = embedding_service.embed_batch(test_texts)
        
        print(f"✅ 成功生成 {len(embeddings)} 个embedding")
        
        # 验证embedding维度
        if embeddings:
            embedding_dim = len(embeddings[0].embedding)
            print(f"📊 Embedding维度: {embedding_dim}")
            
            # 验证维度是否正确（Qwen通常为128维）
            if embedding_dim == 128:
                print("✅ Embedding维度验证通过")
            else:
                print(f"⚠️  Embedding维度异常: 期望128，实际{embedding_dim}")
        
        # 验证配置
        print(f"🔧 服务配置:")
        print(f"   使用Mock模式: {embedding_service.use_mock}")
        if hasattr(embedding_service, 'api_key'):
            print(f"   API密钥配置: {'✅ 已配置' if embedding_service.api_key else '❌ 未配置'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding服务验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_complete_processing_pipeline():
    """测试完整的PDF处理流程"""
    print("\n🔍 测试完整的PDF处理流程...")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        import django
        django.setup()
        
        from apps.pdfloader.models import PDFDocument
        from apps.pdfloader.storage import PDFProcessingPipeline
        from apps.mulvesdb.models import MulvesConnection
        
        # 准备测试文件
        test_pdf_path = Path(__file__).parent / "pdf" / "CASI_RefGuide.pdf"
        if not test_pdf_path.exists():
            print("❌ 测试PDF文件不存在")
            return False
        
        print(f"✅ 测试文件: {test_pdf_path}")
        
        # 获取Milvus连接
        connection = MulvesConnection.objects.get(id=1, is_active=True)
        print(f"✅ 使用Milvus连接: {connection.name}")
        
        # 创建测试文档记录
        pdf_document = PDFDocument.objects.create(
            title="Complete Pipeline Test Document",
            file_path=str(test_pdf_path),
            file_size=test_pdf_path.stat().st_size,
            page_count=0,
            milvus_connection_id=1,
            collection_name="complete_pipeline_test",
            status='uploaded'
        )
        print(f"✅ 创建文档记录，ID: {pdf_document.id}")
        
        # 执行完整处理流程
        print("⚙️  开始完整处理流程...")
        
        async def run_full_pipeline():
            try:
                pipeline = PDFProcessingPipeline(connection.id)
                result = await pipeline.process_pdf_document(pdf_document, str(test_pdf_path))
                print(f"✅ 处理完成: {result}")
                return True
            except Exception as e:
                print(f"❌ 处理失败: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
        
        # 运行处理流程
        result = asyncio.run(run_full_pipeline())
        
        # 检查最终状态
        pdf_document.refresh_from_db()
        print(f"📊 最终文档状态: {pdf_document.status}")
        if pdf_document.error_message:
            print(f"📝 错误信息: {pdf_document.error_message}")
        
        return result and pdf_document.status == 'completed'
        
    except Exception as e:
        print(f"❌ 完整流程测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主验证流程"""
    print("=" * 60)
    print("🔧 PDF处理管道完整验证")
    print("=" * 60)
    
    # 1. 测试Milvus集合创建逻辑
    milvus_ok = test_milvus_collection_logic()
    
    # 2. 验证embedding服务配置
    embedding_ok = test_embedding_service_config()
    
    # 3. 测试完整处理流程
    pipeline_ok = test_complete_processing_pipeline()
    
    print("\n" + "=" * 60)
    print("📋 验证结果总结:")
    print(f"   Milvus集合创建: {'✅ 通过' if milvus_ok else '❌ 失败'}")
    print(f"   Embedding服务: {'✅ 通过' if embedding_ok else '❌ 失败'}")
    print(f"   完整处理流程: {'✅ 通过' if pipeline_ok else '❌ 失败'}")
    
    overall_success = milvus_ok and embedding_ok and pipeline_ok
    print(f"\n🎯 总体结果: {'🎉 全部通过' if overall_success else '💥 存在问题'}")
    
    if not overall_success:
        print("\n🔧 建议修复步骤:")
        if not milvus_ok:
            print("   1. 检查Milvus连接配置和权限")
            print("   2. 验证集合schema定义")
        if not embedding_ok:
            print("   3. 检查Qwen API密钥配置")
            print("   4. 验证网络连接和API访问")
        if not pipeline_ok:
            print("   5. 检查PDF处理管道各组件集成")
            print("   6. 验证错误处理和日志记录")
    
    print("=" * 60)
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)