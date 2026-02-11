"""
PDF Loader 使用示例
展示如何使用PDF Loader的各项功能
"""

import asyncio
import os
from apps.pdfloader.pdf_processor import PDFProcessor
from apps.pdfloader.embedding import get_embedding_service
from apps.pdfloader.storage import PDFProcessingPipeline, PDFVectorStorageService
from apps.pdfloader.models import PDFDocument
from apps.mulvesdb.models import MulvesConnection


def example_basic_pdf_processing():
    """基本PDF处理示例"""
    print("=== 基本PDF处理示例 ===")
    
    # 创建PDF处理器
    processor = PDFProcessor(chunk_size=800, chunk_overlap=100)
    
    # 处理PDF文件（请替换为实际的PDF文件路径）
    pdf_file_path = "sample.pdf"  # 替换为你的PDF文件路径
    
    if os.path.exists(pdf_file_path):
        try:
            # 提取和分块
            chunks = list(processor.process_pdf(pdf_file_path))
            print(f"成功处理PDF文件，生成 {len(chunks)} 个分块")
            
            # 显示前几个分块
            for i, chunk in enumerate(chunks[:3]):
                print(f"分块 {i+1}: {chunk.content[:100]}...")
                
        except Exception as e:
            print(f"PDF处理失败: {e}")
    else:
        print(f"PDF文件不存在: {pdf_file_path}")


def example_embedding_generation():
    """Embedding生成示例"""
    print("\n=== Embedding生成示例 ===")
    
    # 获取embedding服务
    embedding_service = get_embedding_service(use_mock=True)  # 使用mock服务进行演示
    
    # 单个文本embedding
    text = "这是一个测试文本，用于生成embedding向量"
    try:
        result = embedding_service.embed_text(text)
        print(f"文本: {text}")
        print(f"Embedding维度: {len(result.embedding)}")
        print(f"前10维向量: {result.embedding[:10]}")
        
        # 批量embedding
        texts = [
            "第一段测试文本",
            "第二段测试文本", 
            "第三段测试文本"
        ]
        
        results = embedding_service.embed_batch(texts)
        print(f"\n批量处理 {len(results)} 个文本")
        for i, result in enumerate(results):
            print(f"文本 {i+1} 的embedding维度: {len(result.embedding)}")
            
    except Exception as e:
        print(f"Embedding生成失败: {e}")


async def example_vector_storage():
    """向量存储示例"""
    print("\n=== 向量存储示例 ===")
    
    # 假设已有Milvus连接配置
    try:
        # 获取活跃的Milvus连接
        connection = await MulvesConnection.objects.filter(is_active=True).afirst()
        if not connection:
            print("没有可用的Milvus连接配置")
            return
            
        # 创建向量存储服务
        async with PDFVectorStorageService(connection.id) as storage_service:
            collection_name = "example_pdf_collection"
            
            # 创建集合
            try:
                await storage_service.create_document_collection(collection_name)
                print(f"成功创建集合: {collection_name}")
            except Exception as e:
                print(f"创建集合失败: {e}")
                return
            
            # 准备测试数据
            test_chunks = [
                {
                    'content': '人工智能是计算机科学的一个分支',
                    'page_number': 1,
                    'chunk_index': 0,
                    'metadata': {'section': 'introduction'}
                },
                {
                    'content': '机器学习是实现人工智能的方法之一',
                    'page_number': 1,
                    'chunk_index': 1,
                    'metadata': {'section': 'methods'}
                },
                {
                    'content': '深度学习在图像识别领域表现出色',
                    'page_number': 2,
                    'chunk_index': 2,
                    'metadata': {'section': 'applications'}
                }
            ]
            
            # 存储向量数据
            try:
                # 创建测试文档记录
                document = await PDFDocument.objects.acreate(
                    title='测试文档',
                    file_path='/tmp/test.pdf',
                    file_size=1024,
                    page_count=2,
                    milvus_connection=connection,
                    collection_name=collection_name
                )
                
                result = await storage_service.store_pdf_chunks(
                    document_id=document.id,
                    chunks_data=test_chunks,
                    collection_name=collection_name
                )
                
                print(f"成功存储 {result['stored_count']} 个分块向量")
                print(f"总分块数: {result['total_chunks']}")
                print(f"失败分块数: {result['failed_count']}")
                
            except Exception as e:
                print(f"存储向量失败: {e}")
                
    except Exception as e:
        print(f"向量存储示例失败: {e}")


async def example_complete_pipeline():
    """完整处理流水线示例"""
    print("\n=== 完整处理流水线示例 ===")
    
    # 这是一个完整的处理示例，需要实际的PDF文件和Milvus配置
    pdf_file_path = "sample.pdf"  # 替换为实际PDF文件路径
    
    if not os.path.exists(pdf_file_path):
        print(f"示例PDF文件不存在: {pdf_file_path}")
        print("请提供一个实际的PDF文件路径来运行此示例")
        return
    
    try:
        # 获取Milvus连接
        connection = await MulvesConnection.objects.filter(is_active=True).afirst()
        if not connection:
            print("没有可用的Milvus连接配置")
            return
        
        # 创建文档记录
        document = await PDFDocument.objects.acreate(
            title='完整流水线测试文档',
            file_path=pdf_file_path,
            file_size=os.path.getsize(pdf_file_path),
            page_count=0,  # 后续处理时更新
            milvus_connection=connection,
            collection_name='complete_pipeline_test'
        )
        
        print(f"创建文档记录: {document.title}")
        
        # 执行完整处理流水线
        pipeline = PDFProcessingPipeline(connection.id)
        result = await pipeline.process_pdf_document(document, pdf_file_path)
        
        print(f"处理完成:")
        print(f"- 文档ID: {result['document_id']}")
        print(f"- 处理分块数: {result['chunks_processed']}")
        print(f"- 成功存储数: {result['chunks_stored']}")
        print(f"- 存储结果: {result['storage_result']}")
        
    except Exception as e:
        print(f"完整流水线处理失败: {e}")


def example_api_usage():
    """API使用示例"""
    print("\n=== API使用示例 ===")
    
    # 这些示例展示了如何使用API端点
    api_examples = {
        "上传PDF": """
POST /api/pdfloader/upload/
Content-Type: multipart/form-data

Form Data:
- title: "我的文档"
- file: [PDF文件]
- collection_name: "my_collection"
        """,
        
        "获取文档列表": """
GET /api/pdfloader/documents/
Headers: Authorization: Bearer <token>
        """,
        
        "向量搜索": """
POST /api/pdfloader/search/
Content-Type: application/json

{
    "query_text": "搜索相关内容",
    "collection_name": "my_collection",
    "limit": 10
}
        """,
        
        "查询处理状态": """
GET /api/pdfloader/documents/1/status/
        """
    }
    
    for name, example in api_examples.items():
        print(f"\n{name}:")
        print(example)


async def main():
    """运行所有示例"""
    print("PDF Loader 使用示例")
    print("=" * 50)
    
    # 运行同步示例
    example_basic_pdf_processing()
    example_embedding_generation()
    example_api_usage()
    
    # 运行异步示例
    await example_vector_storage()
    await example_complete_pipeline()
    
    print("\n" + "=" * 50)
    print("示例运行完成")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())