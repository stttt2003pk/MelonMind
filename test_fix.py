#!/usr/bin/env python
import os
import sys
import django

# 设置Django环境
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.pdfloader.models import PDFDocument
from apps.mulvesdb.models import MulvesConnection
from apps.pdfloader.storage import PDFProcessingPipeline

def test_fix():
    print("=== 测试修复后的PDF处理流程 ===")
    
    # 获取最新的test集合失败文档
    latest_failed = PDFDocument.objects.filter(status='failed', collection_name='test').order_by('-created_at').first()
    
    if not latest_failed:
        print("没有找到test集合的失败文档")
        return
    
    print(f"测试文档: {latest_failed.title}")
    print(f"文件路径: {latest_failed.file_path}")
    
    if not os.path.exists(latest_failed.file_path):
        print("文件不存在，无法测试")
        return
    
    # 获取Milvus连接
    connection = MulvesConnection.objects.filter(is_active=True).first()
    if not connection:
        print("没有可用的Milvus连接")
        return
    
    print(f"使用连接: {connection.name}")
    
    # 尝试处理
    pipeline = PDFProcessingPipeline(connection.id)
    try:
        print("开始处理...")
        result = pipeline.process_pdf_document(latest_failed, latest_failed.file_path, use_existing_collection=True)
        print(f"✅ 处理成功: {result}")
        
        # 更新文档状态
        latest_failed.status = 'completed'
        latest_failed.save()
        print("✅ 文档状态已更新为完成")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fix()