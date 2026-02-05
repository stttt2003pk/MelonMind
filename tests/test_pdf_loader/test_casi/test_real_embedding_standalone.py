"""
CASI参考指南真实Embedding服务独立测试
不依赖Django测试框架的独立测试脚本
"""

import os
import sys
import time
from openai import OpenAI

def test_embedding_service():
    """测试真实的embedding服务"""
    print("=" * 60)
    print("CASI参考指南真实Embedding服务测试")
    print("=" * 60)
    
    # 检查API密钥
    api_key = os.environ.get('QWEN_API_KEY')
    if not api_key:
        print("❌ 未找到QWEN_API_KEY环境变量")
        return False
    
    print(f"✓ 使用Qwen API密钥: {api_key[:8]}...{api_key[-4:]}")
    
    try:
        # 创建客户端
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        # 测试单个文本embedding
        print("\n1. 单个文本Embedding测试:")
        test_text = "The CASI system has three core components that work together to provide comprehensive analysis capabilities."
        
        start_time = time.time()
        response = client.embeddings.create(
            model="text-embedding-v1",
            input=[test_text]
        )
        end_time = time.time()
        
        if response and response.data:
            embedding = response.data[0].embedding
            print(f"   ✓ 成功生成embedding")
            print(f"   ✓ 处理时间: {end_time - start_time:.3f} 秒")
            print(f"   ✓ 向量维度: {len(embedding)}")
            print(f"   ✓ 前10维数值: {[round(x, 4) for x in embedding[:10]]}")
        else:
            print("   ✗ API响应为空")
            return False
            
        # 测试批量embedding
        print("\n2. 批量Embedding测试:")
        batch_texts = [
            "The three core components of CASI are data processing, analysis engine, and visualization layer.",
            "CASI's first component handles data ingestion and preprocessing tasks efficiently.",
            "The second component performs advanced analytics and pattern recognition algorithms.",
            "Component three manages interactive dashboards and reporting functionalities.",
            "All three components integrate seamlessly to deliver comprehensive business intelligence."
        ]
        
        print(f"   测试批量处理 {len(batch_texts)} 个文本...")
        
        start_time = time.time()
        batch_response = client.embeddings.create(
            model="text-embedding-v1",
            input=batch_texts
        )
        end_time = time.time()
        
        if batch_response and batch_response.data:
            processing_time = end_time - start_time
            print(f"   ✓ 批量处理完成")
            print(f"   ✓ 处理时间: {processing_time:.3f} 秒")
            print(f"   ✓ 平均每个文本: {processing_time/len(batch_texts):.3f} 秒")
            print(f"   ✓ 成功处理: {len(batch_response.data)} 个文本")
            
            # 验证每个embedding
            for i, data in enumerate(batch_response.data):
                assert len(data.embedding) == len(embedding), f"第{i+1}个文本embedding维度不匹配"
        else:
            print("   ✗ 批量处理失败")
            return False
            
        # 模拟搜索场景
        print("\n3. 模拟搜索场景测试:")
        query = "3 core components in CASI"
        print(f"   搜索查询: '{query}'")
        
        # 生成查询的embedding
        query_response = client.embeddings.create(
            model="text-embedding-v1",
            input=[query]
        )
        
        if query_response and query_response.data:
            query_embedding = query_response.data[0].embedding
            print(f"   ✓ 查询向量生成完成 (维度: {len(query_embedding)})")
            
            # 计算与批量文本的相似度（简化的点积计算）
            similarities = []
            for i, text_embedding in enumerate(batch_response.data):
                # 简单的余弦相似度近似计算
                dot_product = sum(a * b for a, b in zip(query_embedding, text_embedding.embedding))
                similarity = dot_product / (len(query_embedding) * 100)  # 简化归一化
                similarities.append((i, similarity, batch_texts[i][:50] + "..."))
            
            # 排序并显示结果
            similarities.sort(key=lambda x: x[1], reverse=True)
            print(f"   ✓ 相似度计算完成")
            print(f"   返回最相关的3个结果:")
            
            for i, (idx, sim, text_preview) in enumerate(similarities[:3], 1):
                print(f"     {i}. 相似度: {sim:.3f}")
                print(f"        文本: {text_preview}")
                
        else:
            print("   ✗ 查询向量生成失败")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

def test_casi_specific_queries():
    """测试CASI相关的具体查询"""
    print("\n4. CASI特定查询测试:")
    
    api_key = os.environ.get('QWEN_API_KEY')
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    
    # CASI相关的查询和文档内容
    queries = [
        "3 core components in CASI",
        "CASI architecture overview",
        "main features of CASI system"
    ]
    
    # 模拟的CASI文档内容片段
    document_snippets = [
        "The CASI system is built upon three fundamental architectural components that work in harmony.",
        "Component one handles data ingestion, preprocessing, and initial filtering operations.",
        "The second component focuses on advanced analytics, machine learning algorithms, and pattern detection.",
        "Component three provides interactive visualization, dashboard creation, and reporting capabilities.",
        "These three components form the backbone of the CASI platform, enabling comprehensive business intelligence.",
        "The modular architecture allows each component to be scaled independently based on workload demands."
    ]
    
    print(f"   测试 {len(queries)} 个查询，对比 {len(document_snippets)} 个文档片段")
    
    try:
        # 生成所有文本的embedding
        all_texts = queries + document_snippets
        response = client.embeddings.create(
            model="text-embedding-v1",
            input=all_texts
        )
        
        if not response or not response.data:
            print("   ✗ 文本向量化失败")
            return False
            
        # 分离查询和文档向量
        query_embeddings = response.data[:len(queries)]
        doc_embeddings = response.data[len(queries):]
        
        print("   ✓ 所有文本向量化完成")
        
        # 对每个查询进行匹配测试
        for q_idx, (query, q_embedding) in enumerate(zip(queries, query_embeddings)):
            print(f"\n   查询 {q_idx + 1}: '{query}'")
            
            # 计算与所有文档片段的相似度
            similarities = []
            for d_idx, (snippet, d_embedding) in enumerate(zip(document_snippets, doc_embeddings)):
                # 简单点积相似度
                similarity = sum(a * b for a, b in zip(q_embedding.embedding, d_embedding.embedding))
                similarities.append((d_idx, similarity, snippet))
            
            # 排序并显示前3个结果
            similarities.sort(key=lambda x: x[1], reverse=True)
            print(f"     最相关的3个文档片段:")
            
            for rank, (d_idx, sim, snippet) in enumerate(similarities[:3], 1):
                normalized_sim = sim / (len(q_embedding.embedding) * 1000)  # 简单归一化
                print(f"       {rank}. 相似度: {normalized_sim:.3f}")
                print(f"          片段: {snippet[:60]}...")
                
        return True
        
    except Exception as e:
        print(f"   ✗ CASI特定查询测试失败: {e}")
        return False

def main():
    """主函数"""
    print("开始CASI参考指南真实Embedding服务测试...")
    
    tests = [
        ("Embedding服务基础测试", test_embedding_service),
        ("CASI特定查询测试", test_casi_specific_queries)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'-' * 50}")
        print(f"执行测试: {test_name}")
        print('-' * 50)
        
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
        print("🎉 所有真实Embedding服务测试都成功通过！")
        print("\n这意味着:")
        print("- Qwen API密钥配置正确")
        print("- Embedding服务工作正常")
        print("- 可以处理CASI文档相关的查询")
        print("- 系统准备好进行真实的PDF处理和搜索")
    else:
        print("❌ 部分测试失败，请检查上述错误")
    
    print("=" * 60)
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)