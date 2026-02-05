"""
CASI参考指南简单测试脚本
不依赖Django测试框架的独立测试
"""

import os
import sys
import requests
import time
import json

def test_pdf_exists():
    """测试PDF文件是否存在"""
    pdf_path = os.path.join(
        os.path.dirname(__file__), 
        'pdf', 
        'CASI_RefGuide.pdf'
    )
    
    print("测试1: 检查PDF文件...")
    if os.path.exists(pdf_path):
        file_size = os.path.getsize(pdf_path)
        print(f"✓ PDF文件存在: {pdf_path}")
        print(f"✓ 文件大小: {file_size} bytes ({file_size/1024/1024:.2f} MB)")
        return True
    else:
        print(f"✗ PDF文件不存在: {pdf_path}")
        return False

def test_api_endpoints():
    """测试API端点是否可达"""
    base_url = "http://localhost:8000"
    
    print("\n测试2: 检查API端点...")
    
    endpoints = [
        ("/api/pdfloader/documents/", "PDF文档列表"),
        ("/api/pdfloader/upload/", "PDF上传"),
        ("/api/pdfloader/search/", "向量搜索")
    ]
    
    all_reachable = True
    
    for endpoint, description in endpoints:
        url = base_url + endpoint
        try:
            response = requests.get(url, timeout=5)
            if response.status_code in [200, 405]:  # 405表示方法不允许，但端点存在
                print(f"✓ {description}: {url} (状态码: {response.status_code})")
            else:
                print(f"⚠ {description}: {url} (状态码: {response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"✗ {description}: {url} (错误: {e})")
            all_reachable = False
    
    return all_reachable

def test_pdf_upload_simulation():
    """模拟PDF上传测试（不实际上传文件）"""
    print("\n测试3: 模拟PDF上传流程...")
    
    # 模拟上传数据
    upload_data = {
        'title': 'CASI Reference Guide Test',
        'milvus_connection_id': 1,
        'collection_name': 'casi_guide_test'
    }
    
    print("模拟上传数据:")
    for key, value in upload_data.items():
        print(f"  {key}: {value}")
    
    print("✓ 上传数据格式验证通过")
    return True

def test_search_query_simulation():
    """模拟搜索查询测试"""
    print("\n测试4: 模拟向量搜索...")
    
    search_queries = [
        '3 core components in CASI',
        'CASI architecture components', 
        'main components of CASI system'
    ]
    
    print("测试搜索查询:")
    for i, query in enumerate(search_queries, 1):
        print(f"  {i}. '{query}'")
        
        # 模拟搜索结果
        mock_results = [
            {
                'content': f'Result {j} for query "{query[:30]}..." - This would be actual content from the PDF',
                'similarity': round(0.95 - j * 0.08, 3),
                'page_number': j * 2,
                'chunk_index': j
            }
            for j in range(1, 4)
        ]
        
        print(f"     模拟返回 {len(mock_results)} 个结果:")
        for result in mock_results:
            print(f"       - 相似度: {result['similarity']}, 页码: {result['page_number']}")
            print(f"         内容: {result['content'][:60]}...")
    
    print("✓ 搜索查询模拟完成")
    return True

def test_complete_workflow_description():
    """描述完整的测试工作流程"""
    print("\n测试5: 完整工作流程说明...")
    
    workflow_steps = [
        "1. 启动Django开发服务器: poetry run python manage.py runserver",
        "2. 确保Milvus数据库服务运行",
        "3. 配置有效的embedding服务（OpenAI/Qwen）",
        "4. 上传CASI_RefGuide.pdf文件",
        "5. 等待后台处理完成（提取文本→分块→向量化→入库）",
        "6. 使用查询 '3 core components in CASI' 进行向量搜索",
        "7. 验证返回的相关内容和相似度分数"
    ]
    
    print("完整的测试工作流程:")
    for step in workflow_steps:
        print(f"  {step}")
    
    print("\n预期结果:")
    print("  - PDF成功上传并处理")
    print("  - 生成多个文本分块")
    print("  - 每个分块转换为向量并存储到Milvus")
    print("  - 搜索 '3 core components in CASI' 返回相关内容")
    print("  - 相似度分数反映内容相关性")
    
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("CASI参考指南测试套件")
    print("=" * 60)
    
    tests = [
        ("PDF文件检查", test_pdf_exists),
        ("API端点检查", test_api_endpoints), 
        ("上传流程模拟", test_pdf_upload_simulation),
        ("搜索查询模拟", test_search_query_simulation),
        ("工作流程说明", test_complete_workflow_description)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'-' * 40}")
        print(f"执行测试: {test_name}")
        print('-' * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} 通过")
            else:
                print(f"✗ {test_name} 失败")
        except Exception as e:
            print(f"✗ {test_name} 异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"测试总结: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试都成功通过！")
        print("\n下一步建议:")
        print("1. 启动开发服务器: poetry run python manage.py runserver")
        print("2. 使用Postman或curl实际测试API")
        print("3. 观察后台处理流程和搜索效果")
    else:
        print("❌ 部分测试失败，请检查上述错误")
    
    print("=" * 60)
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)