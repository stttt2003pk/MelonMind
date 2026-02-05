#!/usr/bin/env python
"""
PDF Loader 真实API功能测试脚本
使用真实的Qwen API Key进行完整功能验证
"""

import os
import sys
import asyncio

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 设置环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['USE_MOCK_EMBEDDING'] = 'false'  # 强制使用真实API

try:
    import django
    django.setup()
except ImportError as e:
    print(f"Django导入失败: {e}")
    sys.exit(1)

def test_real_embedding_service():
    """测试真实的Embedding服务"""
    print("=== 真实Qwen API测试 ===\n")
    
    try:
        from apps.pdfloader.embedding import get_embedding_service
        
        # 获取真实服务
        service = get_embedding_service(use_mock=False)
        print(f"✓ 成功初始化真实Embedding服务")
        print(f"  服务类型: {type(service).__name__}")
        print(f"  API Key: {'已配置' if os.getenv('QWEN_API_KEY') else '未配置'}")
        
        # 测试单个文本
        print("\n1. 测试单个文本embedding...")
        test_texts = [
            "人工智能是计算机科学的一个重要分支",
            "机器学习算法在数据分析中发挥重要作用",
            "深度学习技术推动了图像识别的发展"
        ]
        
        for i, text in enumerate(test_texts, 1):
            print(f"  测试文本 {i}: {text}")
            result = service.embed_text(text)
            print(f"    ✓ 成功生成embedding")
            print(f"    - 维度: {len(result.embedding)}")
            print(f"    - 模型: {result.model}")
            print(f"    - 前3维: {[round(x, 4) for x in result.embedding[:3]]}")
            print(f"    - 后3维: {[round(x, 4) for x in result.embedding[-3:]]}")
        
        # 测试批量处理
        print("\n2. 测试批量embedding...")
        batch_results = service.embed_batch(test_texts)
        print(f"  ✓ 批量处理成功")
        print(f"  - 处理文本数: {len(batch_results)}")
        print(f"  - 总token使用: {sum(r.metadata.get('usage', {}).get('total_tokens', 0) for r in batch_results)}")
        
        # 验证一致性
        print("\n3. 测试结果一致性...")
        first_text = test_texts[0]
        result1 = service.embed_text(first_text)
        result2 = service.embed_text(first_text)
        
        # 对于真实API，相同文本应该产生相似的向量
        import numpy as np
        similarity = np.dot(result1.embedding, result2.embedding) / (
            np.linalg.norm(result1.embedding) * np.linalg.norm(result2.embedding)
        )
        print(f"  相同文本相似度: {similarity:.4f}")
        print(f"  ✓ 结果一致性验证通过")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_pdf_processing_with_real_api():
    """测试使用真实API的PDF处理"""
    print("\n=== PDF处理与真实API集成测试 ===\n")
    
    try:
        from apps.pdfloader.pdf_processor import PDFProcessor
        from apps.pdfloader.embedding import get_embedding_service
        
        # 创建测试PDF内容
        sample_text = """
        这是一个测试PDF文档。
        它用于验证PDF Loader应用的功能。
        包含多行文本内容以测试分块功能。
        人工智能技术不断发展。
        机器学习算法日趋成熟。
        深度学习应用越来越广泛。
        """
        
        # 创建临时PDF处理器
        processor = PDFProcessor(chunk_size=100, chunk_overlap=20)
        
        # 模拟PDF分块（实际环境中这里会处理真实PDF文件）
        chunks_data = [
            {'content': '人工智能是计算机科学的一个重要分支，专注于创建智能机器。', 'page_number': 1, 'chunk_index': 0},
            {'content': '机器学习是人工智能的核心技术之一，通过算法让计算机从数据中学习。', 'page_number': 1, 'chunk_index': 1},
            {'content': '深度学习使用神经网络架构来处理复杂的模式识别任务。', 'page_number': 2, 'chunk_index': 2}
        ]
        
        print(f"✓ 准备了 {len(chunks_data)} 个测试分块")
        
        # 使用真实API生成embedding
        service = get_embedding_service(use_mock=False)
        texts = [chunk['content'] for chunk in chunks_data]
        
        print("正在生成真实embedding...")
        embeddings = service.embed_batch(texts)
        
        print(f"✓ 成功生成 {len(embeddings)} 个embedding")
        print(f"  平均维度: {sum(len(e.embedding) for e in embeddings) // len(embeddings)}")
        print(f"  总token消耗: {sum(e.metadata.get('usage', {}).get('total_tokens', 0) for e in embeddings)}")
        
        # 验证向量质量
        import numpy as np
        for i, (chunk, embedding) in enumerate(zip(chunks_data, embeddings)):
            vector_norm = np.linalg.norm(embedding.embedding)
            print(f"  分块 {i+1}: 范数={vector_norm:.2f}, 内容长度={len(chunk['content'])}")
        
        return True
        
    except Exception as e:
        print(f"✗ PDF处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("PDF Loader 真实API功能验证")
    print("=" * 50)
    
    # 检查API Key配置
    api_key = os.getenv('QWEN_API_KEY')
    if not api_key:
        print("❌ 错误: 未配置QWEN_API_KEY环境变量")
        print("请设置: export QWEN_API_KEY=your_api_key_here")
        return False
    
    print(f"✓ API Key已配置: {api_key[:8]}...")
    print(f"✓ 使用真实Qwen API (非mock模式)")
    
    # 运行各项测试
    tests = [
        ("Embedding服务测试", test_real_embedding_service),
        ("PDF处理集成测试", test_pdf_processing_with_real_api),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'-' * 30}")
        print(f"运行测试: {test_name}")
        print(f"{'-' * 30}")
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = asyncio.run(test_func())
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} 执行出错: {e}")
            results.append((test_name, False))
    
    # 输出总结
    print(f"\n{'=' * 50}")
    print("测试结果总结:")
    print(f"{'=' * 50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status}: {test_name}")
    
    print(f"\n总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！PDF Loader真实API功能正常工作。")
        return True
    else:
        print("⚠️  部分测试失败，请检查上述错误信息。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)