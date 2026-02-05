#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版PDF处理测试 - 直接调用核心功能而不通过API
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def test_direct_pdf_processing():
    """直接测试PDF处理核心功能"""
    print("🔬 开始直接PDF处理测试...")
    
    try:
        # 导入必要的模块
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        import django
        django.setup()
        
        from apps.pdfloader.models import PDFDocument
        from apps.pdfloader.storage import PDFProcessingPipeline
        from apps.mulvesdb.models import MulvesConnection
        
        # 测试PDF文件路径
        test_pdf_path = Path(__file__).parent / "pdf" / "CASI_RefGuide.pdf"
        
        if not test_pdf_path.exists():
            print(f"❌ 测试PDF文件不存在: {test_pdf_path}")
            return False
        
        print(f"✅ 找到测试文件: {test_pdf_path}")
        
        # 获取Milvus连接
        try:
            milvus_connection = MulvesConnection.objects.get(id=1, is_active=True)
            print(f"✅ Milvus连接可用: {milvus_connection.name}")
        except MulvesConnection.DoesNotExist:
            print("❌ Milvus连接不存在")
            return False
        
        # 创建PDF文档记录
        print("\n📝 创建PDF文档记录...")
        pdf_document = PDFDocument.objects.create(
            title="Direct Test Document",
            file_path=str(test_pdf_path),
            file_size=test_pdf_path.stat().st_size,
            page_count=0,
            milvus_connection_id=1,
            collection_name="direct_test_collection",
            status='uploaded'
        )
        print(f"✅ 文档记录创建成功，ID: {pdf_document.id}")
        
        # 直接调用处理管道
        print("\n⚙️  开始PDF处理...")
        import asyncio
        
        async def run_processing():
            pipeline = PDFProcessingPipeline(milvus_connection.id)
            try:
                result = await pipeline.process_pdf_document(pdf_document, str(test_pdf_path))
                print(f"✅ PDF处理完成: {result}")
                return True
            except Exception as e:
                print(f"❌ PDF处理失败: {str(e)}")
                pdf_document.mark_as_failed(str(e))
                return False
        
        # 运行异步处理
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(run_processing())
        loop.close()
        
        if success:
            print("\n🎉 直接PDF处理测试成功!")
            return True
        else:
            print("\n💥 直接PDF处理测试失败!")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_direct_pdf_processing()
    sys.exit(0 if success else 1)