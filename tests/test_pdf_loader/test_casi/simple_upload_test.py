#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版PDF上传测试 - 绕过复杂异步处理
"""

import os
import sys
import tempfile
from pathlib import Path
import requests

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def test_simple_upload_only():
    """只测试文件上传，不触发后台处理"""
    print("📤 简化版文件上传测试...")
    
    # 服务器配置
    base_url = "http://127.0.0.1:8000"
    api_prefix = "/api/pdfloader"
    
    # 测试PDF文件路径
    test_pdf_path = Path(__file__).parent / "pdf" / "CASI_RefGuide.pdf"
    
    if not test_pdf_path.exists():
        print(f"❌ 测试PDF文件不存在: {test_pdf_path}")
        return False
    
    print(f"✅ 找到测试文件: {test_pdf_path}")
    print(f"📄 文件大小: {test_pdf_path.stat().st_size} bytes")
    
    try:
        # 只上传文件，不触发处理
        print("\n📤 上传PDF文件（仅上传）...")
        with open(test_pdf_path, 'rb') as pdf_file:
            upload_data = {
                'title': 'Simple Upload Test',
                'milvus_connection_id': 1,
                'collection_name': 'simple_test_collection'
            }
            files = {'file': ('CASI_RefGuide.pdf', pdf_file, 'application/pdf')}
            
            upload_response = requests.post(
                f"{base_url}{api_prefix}/upload/",
                data=upload_data,
                files=files,
                timeout=30
            )
            
            print(f"📊 上传响应状态: {upload_response.status_code}")
            print(f"📄 响应内容: {upload_response.text[:200]}...")
            
            if upload_response.status_code == 201:
                result = upload_response.json()
                document_id = result.get('data', {}).get('id')
                file_path = result.get('data', {}).get('file_path')
                print(f"✅ 文件上传成功")
                print(f"   文档ID: {document_id}")
                print(f"   文件路径: {file_path}")
                
                # 验证文件是否真的存在
                if file_path and os.path.exists(file_path):
                    actual_size = os.path.getsize(file_path)
                    print(f"   实际文件大小: {actual_size} bytes")
                    print(f"   大小匹配: {actual_size == test_pdf_path.stat().st_size}")
                else:
                    print(f"   ⚠️  文件路径无效或文件不存在")
                
                return True
            else:
                print(f"❌ 上传失败: {upload_response.text}")
                return False
                
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verify_uploaded_files():
    """验证已上传的文件状态"""
    print("\n🔍 验证已上传文件状态...")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        import django
        django.setup()
        
        from apps.pdfloader.models import PDFDocument
        
        # 查看最近上传的文档
        recent_docs = PDFDocument.objects.order_by('-created_at')[:5]
        print(f"最近 {len(recent_docs)} 个文档:")
        
        for doc in recent_docs:
            print(f"\n=== 文档 ID: {doc.id} ===")
            print(f"标题: {doc.title}")
            print(f"文件路径: {doc.file_path}")
            print(f"状态: {doc.status}")
            print(f"文件大小: {doc.file_size} bytes")
            
            # 检查文件是否存在
            if doc.file_path and os.path.exists(doc.file_path):
                actual_size = os.path.getsize(doc.file_path)
                print(f"实际文件大小: {actual_size} bytes")
                print(f"大小一致性: {'✅' if actual_size == doc.file_size else '❌'}")
            else:
                print("文件不存在: ❌")
                
    except Exception as e:
        print(f"验证过程中出错: {str(e)}")

if __name__ == "__main__":
    print("=" * 50)
    success = test_simple_upload_only()
    verify_uploaded_files()
    print("=" * 50)
    print(f"最终结果: {'✅ 成功' if success else '❌ 失败'}")
    sys.exit(0 if success else 1)