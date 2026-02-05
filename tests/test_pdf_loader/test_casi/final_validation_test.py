#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终PDF处理管道验证测试
验证所有修复后功能的完整工作流程
"""

import os
import sys
import asyncio
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def final_validation_test():
    """最终验证测试"""
    print("🏁 最终PDF处理管道验证测试")
    print("=" * 50)
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        import django
        django.setup()
        
        from apps.pdfloader.models import PDFDocument
        from apps.pdfloader.storage import PDFProcessingPipeline
        from apps.mulvesdb.models import MulvesConnection
        from apps.pdfloader.embedding import get_embedding_service
        
        # 1. 验证基础组件
        print("1️⃣ 验证基础组件...")
        
        # Embedding服务
        embedding_service = get_embedding_service()
        print(f"   ✅ Embedding服务: {type(embedding_service).__name__}")
        
        # Milvus连接
        connection = MulvesConnection.objects.get(id=1, is_active=True)
        print(f"   ✅ Milvus连接: {connection.name} ({connection.host}:{connection.port})")
        
        # 测试文件
        test_pdf_path = Path(__file__).parent / "pdf" / "CASI_RefGuide.pdf"
        if not test_pdf_path.exists():
            print("   ❌ 测试PDF文件不存在")
            return False
        print(f"   ✅ 测试文件: {test_pdf_path.name}")
        
        # 2. 测试Milvus集合操作
        print("\n2️⃣ 测试Milvus集合操作...")
        from apps.mulvesdb.connectors import MulvesDBConnector
        connector = MulvesDBConnector(connection)
        
        async def test_milvus_operations():
            await connector.connect()
            print("   ✅ Milvus连接成功")
            
            # 创建测试集合
            test_collection = f"final_test_{int(time.time())}"
            fields = [
                {
                    "name": "id",
                    "type": "INT64",
                    "is_primary": True,
                    "auto_id": True
                },
                {
                    "name": "content",
                    "type": "VARCHAR",
                    "max_length": 1000
                },
                {
                    "name": "embedding",
                    "type": "FLOAT_VECTOR",
                    "dim": 128  # 指定向量维度
                }
            ]
            
            # 创建集合
            connector._milvus_client.create_collection(
                collection_name=test_collection,
                fields=fields
            )
            print(f"   ✅ 创建集合: {test_collection}")
            
            # 验证创建
            collections = connector._milvus_client.list_collections()
            if test_collection in collections:
                print("   ✅ 集合创建验证通过")
                
                # 插入测试数据
                test_data = [
                    {
                        "content": "This is test document content for validation",
                        "embedding": [0.1] * 128  # 128维向量
                    }
                ]
                
                result = connector._milvus_client.insert(
                    collection_name=test_collection,
                    data=test_data
                )
                print(f"   ✅ 数据插入成功，插入数量: {len(test_data)}")
                
                # 清理测试集合
                connector._milvus_client.drop_collection(test_collection)
                print(f"   🗑️  清理测试集合: {test_collection}")
            
            await connector.disconnect()
            return True
            
        milvus_success = asyncio.run(test_milvus_operations())
        if not milvus_success:
            print("   ❌ Milvus操作测试失败")
            return False
            
        # 3. 测试完整PDF处理流程
        print("\n3️⃣ 测试完整PDF处理流程...")
        
        # 创建文档记录
        pdf_document = PDFDocument.objects.create(
            title="Final Validation Test Document",
            file_path=str(test_pdf_path),
            file_size=test_pdf_path.stat().st_size,
            page_count=0,
            milvus_connection_id=1,
            collection_name=f"final_validation_{int(time.time())}",
            status='uploaded'
        )
        print(f"   ✅ 创建文档记录，ID: {pdf_document.id}")
        
        # 执行处理流程
        async def run_processing_pipeline():
            try:
                pipeline = PDFProcessingPipeline(connection.id)
                result = await pipeline.process_pdf_document(pdf_document, str(test_pdf_path))
                print(f"   ✅ 处理完成: {result}")
                return True
            except Exception as e:
                print(f"   ❌ 处理失败: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
                
        processing_success = asyncio.run(run_processing_pipeline())
        
        # 检查最终状态
        pdf_document.refresh_from_db()
        print(f"   📊 最终状态: {pdf_document.status}")
        if pdf_document.status == 'completed':
            print("   ✅ 处理流程成功完成")
        elif pdf_document.error_message:
            print(f"   ⚠️  处理遇到错误: {pdf_document.error_message}")
            
        # 4. 验证结果
        print("\n4️⃣ 验证最终结果...")
        overall_success = (
            milvus_success and 
            processing_success and 
            pdf_document.status == 'completed'
        )
        
        return overall_success
        
    except Exception as e:
        print(f"❌ 验证测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    success = final_validation_test()
    
    print("\n" + "=" * 50)
    print("🎯 最终验证结果:")
    if success:
        print("🎉 PDF处理管道验证通过！")
        print("✅ 所有组件工作正常")
        print("✅ 完整处理流程成功执行")
    else:
        print("💥 验证未通过，请检查上述错误")
        
    print("=" * 50)
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)