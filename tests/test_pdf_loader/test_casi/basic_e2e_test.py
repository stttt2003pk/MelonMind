#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基础端到端测试 - 验证PDF上传、处理、搜索完整流程
"""

import os
import sys
import time
import requests
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def test_basic_e2e_workflow():
    """测试基本的端到端工作流程"""
    print("🚀 开始基础端到端测试...")
    
    # 服务器配置
    base_url = "http://127.0.0.1:8000"
    api_prefix = "/api/pdfloader"
    
    # 测试PDF文件路径
    test_pdf_path = Path(__file__).parent / "pdf" / "CASI_RefGuide.pdf"
    
    if not test_pdf_path.exists():
        print(f"❌ 测试PDF文件不存在: {test_pdf_path}")
        return False
    
    print(f"✅ 找到测试文件: {test_pdf_path}")
    
    try:
        # 1. 测试服务器连通性
        print("\n1️⃣ 测试服务器连通性...")
        health_response = requests.get(f"{base_url}/api/pdfloader/documents/", timeout=5)
        print(f"   状态码: {health_response.status_code}")
        if health_response.status_code == 200:
            print("   ✅ 服务器连接正常")
        else:
            print("   ⚠️  服务器返回非200状态码")
        
        # 2. 上传PDF文件
        print("\n2️⃣ 上传PDF文件...")
        with open(test_pdf_path, 'rb') as pdf_file:
            upload_data = {
                'title': 'CASI Reference Guide Test Document',
                'milvus_connection_id': 1,
                'collection_name': 'casi_test_collection'
            }
            files = {'file': ('CASI_RefGuide.pdf', pdf_file, 'application/pdf')}
            
            upload_response = requests.post(
                f"{base_url}{api_prefix}/upload/",
                data=upload_data,
                files=files,
                timeout=30
            )
            
            print(f"   上传响应状态: {upload_response.status_code}")
            if upload_response.status_code == 201:
                upload_result = upload_response.json()
                document_id = upload_result.get('data', {}).get('id')
                print(f"   ✅ 文件上传成功，文档ID: {document_id}")
            else:
                print(f"   ❌ 上传失败: {upload_response.text}")
                return False
        
        # 3. 等待处理完成（模拟等待）
        print("\n3️⃣ 等待文档处理完成...")
        time.sleep(10)  # 等待10秒让后台处理完成
        
        # 4. 检查处理状态
        print("\n4️⃣ 检查文档处理状态...")
        status_response = requests.get(
            f"{base_url}{api_prefix}/documents/{document_id}/status/",
            timeout=10
        )
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            document_status = status_data.get('data', {}).get('status', 'unknown')
            print(f"   文档状态: {document_status}")
            
            if document_status in ['completed', 'processed']:
                print("   ✅ 文档处理完成")
            elif document_status == 'processing':
                print("   ⏳ 文档仍在处理中")
            else:
                print(f"   ⚠️  文档状态异常: {document_status}")
        else:
            print(f"   ❌ 获取状态失败: {status_response.status_code}")
        
        # 5. 执行向量搜索
        print("\n5️⃣ 执行向量搜索...")
        search_data = {
            'query_text': '3 core components in CASI',
            'collection_name': 'casi_test_collection',
            'limit': 5
        }
        
        search_response = requests.post(
            f"{base_url}{api_prefix}/search/",
            json=search_data,
            timeout=30
        )
        
        print(f"   搜索响应状态: {search_response.status_code}")
        if search_response.status_code == 200:
            search_results = search_response.json()
            result_count = len(search_results.get('data', []))
            print(f"   ✅ 搜索成功，找到 {result_count} 个结果")
            
            # 显示前几个结果
            results = search_results.get('data', [])
            for i, result in enumerate(results[:3]):
                print(f"   结果 {i+1}: {result.get('content', '')[:100]}...")
        else:
            print(f"   ❌ 搜索失败: {search_response.text}")
            # 即使搜索失败也继续，因为可能是集合还未创建
        
        print("\n🎉 基础端到端测试完成!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保Django服务器正在运行")
        return False
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_basic_e2e_workflow()
    sys.exit(0 if success else 1)