#!/usr/bin/env python
"""
PDF Chunking模式演示脚本
展示当前的分块策略和效果
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    import django
    django.setup()
except ImportError as e:
    print(f"Django导入失败: {e}")
    sys.exit(1)

def demonstrate_chunking_strategy():
    """演示分块策略"""
    print("=== PDF Loader Chunking策略演示 ===\n")
    
    from apps.pdfloader.pdf_processor import PDFProcessor
    
    # 创建不同配置的处理器
    processors = [
        ("默认配置", PDFProcessor(chunk_size=1000, chunk_overlap=200)),
        ("小块配置", PDFProcessor(chunk_size=200, chunk_overlap=50)),
        ("大块配置", PDFProcessor(chunk_size=2000, chunk_overlap=300)),
    ]
    
    # 测试文本（模拟PDF内容）
    sample_text = """
人工智能是计算机科学的一个重要分支，专注于创建能够执行通常需要人类智能才能完成的任务的系统。

机器学习作为人工智能的核心技术，通过算法使计算机能够从数据中自动学习和改进，而无需明确编程。

深度学习是机器学习的一个子领域，它使用多层神经网络来模拟人脑的学习过程，特别擅长处理图像识别、语音识别和自然语言处理等复杂任务。

自然语言处理技术使得计算机能够理解和生成人类语言，这在智能客服、机器翻译和文本分析等领域有着广泛应用。

计算机视觉技术赋予机器"看"的能力，能够识别和理解图像及视频内容，在医疗影像分析、自动驾驶和安防监控等方面发挥重要作用。
"""
    
    print("原始文本长度:", len(sample_text), "字符")
    print("原始文本预览:")
    print("-" * 50)
    print(sample_text[:200] + "..." if len(sample_text) > 200 else sample_text)
    print("-" * 50)
    
    for config_name, processor in processors:
        print(f"\n📊 {config_name} (chunk_size={processor.chunk_size}, overlap={processor.chunk_overlap}):")
        print("=" * 60)
        
        # 模拟页面数据
        pages_data = [{
            'page_number': 1,
            'text': sample_text,
            'word_count': len(sample_text.split())
        }]
        
        # 执行分块
        chunks = list(processor.chunk_text(pages_data))
        
        print(f"生成分块数量: {len(chunks)}")
        print(f"平均每块长度: {sum(len(chunk.content) for chunk in chunks) // len(chunks)} 字符")
        
        # 显示前几个分块的详细信息
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n🔸 分块 {i+1}:")
            print(f"   长度: {len(chunk.content)} 字符")
            print(f"   页码: {chunk.page_number}")
            print(f"   内容预览: {chunk.content[:100]}...")
            
            # 显示重叠信息（如果不是第一个分块）
            if i > 0:
                prev_chunk = chunks[i-1]
                # 简单的重叠检测
                overlap_chars = min(len(prev_chunk.content), len(chunk.content))
                if overlap_chars > 0:
                    prev_suffix = prev_chunk.content[-overlap_chars:] if len(prev_chunk.content) >= overlap_chars else prev_chunk.content
                    curr_prefix = chunk.content[:overlap_chars] if len(chunk.content) >= overlap_chars else chunk.content
                    # 计算相似度作为重叠指示
                    if prev_suffix and curr_prefix:
                        import difflib
                        similarity = difflib.SequenceMatcher(None, prev_suffix[-50:], curr_prefix[:50]).ratio()
                        print(f"   与前一分块重叠度: ~{similarity:.1%}")

def analyze_separators_effect():
    """分析分隔符效果"""
    print("\n\n=== 分隔符策略分析 ===\n")
    
    from apps.pdfloader.pdf_processor import RecursiveCharacterTextSplitter
    
    # 测试不同类型的文本
    test_cases = [
        ("段落文本", "第一段内容。\n\n第二段内容。\n\n第三段内容。"),
        ("列表文本", "• 项目一\n• 项目二\n• 项目三"),
        ("连续文本", "这是连续的文本内容没有任何明显的分割符只是简单地连接在一起形成一个长句子"),
        ("混合文本", "标题\n\n正文内容第一部分。这里是更多的内容和信息。\n\n另一个段落开始了。")
    ]
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=50,
        chunk_overlap=10,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    for case_name, text in test_cases:
        print(f"📋 {case_name}:")
        print(f"   原文: {repr(text)}")
        print(f"   长度: {len(text)} 字符")
        
        chunks = splitter.split_text(text)
        print(f"   分块结果 ({len(chunks)} 块):")
        for i, chunk in enumerate(chunks):
            print(f"     [{i+1}] {repr(chunk)}")
        print()

def show_current_recommendations():
    """显示当前推荐配置"""
    print("\n\n=== 当前推荐配置 ===\n")
    
    recommendations = {
        "技术文档": {
            "chunk_size": 800,
            "chunk_overlap": 150,
            "理由": "技术文档通常有清晰的结构，较小的块有助于精确定位"
        },
        "学术论文": {
            "chunk_size": 1200,
            "chunk_overlap": 200,
            "理由": "学术内容较长且复杂，需要更大的上下文窗口"
        },
        "小说/文学作品": {
            "chunk_size": 1500,
            "chunk_overlap": 300,
            "理由": "叙事性文本需要保持故事情节的连贯性"
        },
        "法律文档": {
            "chunk_size": 1000,
            "chunk_overlap": 250,
            "理由": "法律条文精确性强，需要较多重叠确保完整性"
        }
    }
    
    for doc_type, config in recommendations.items():
        print(f"📚 {doc_type}:")
        print(f"   分块大小: {config['chunk_size']} 字符")
        print(f"   重叠大小: {config['chunk_overlap']} 字符")
        print(f"   推荐理由: {config['理由']}")
        print()

if __name__ == "__main__":
    demonstrate_chunking_strategy()
    analyze_separators_effect()
    show_current_recommendations()
    
    print("\n💡 总结:")
    print("• 当前使用LangChain的RecursiveCharacterTextSplitter")
    print("• 默认配置: chunk_size=1000, chunk_overlap=200")
    print("• 分隔符优先级: 段落 > 行 > 词 > 字符")
    print("• 重叠机制确保语义完整性")
    print("• 可根据不同文档类型调整参数获得最佳效果")