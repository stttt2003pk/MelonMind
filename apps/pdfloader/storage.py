import logging
import uuid
from typing import List, Dict, Any
from datetime import datetime
from django.db import transaction
from apps.mulvesdb.connectors import MulvesDBConnector
from apps.mulvesdb.models import MulvesConnection
from .models import PDFDocument, PDFChunk
from .embedding import get_embedding_service, EmbeddingResult
import logging

logger = logging.getLogger(__name__)


class PDFVectorStorageService:
    """PDF向量存储服务"""
    
    def __init__(self, milvus_connection_id: int):
        """
        初始化向量存储服务
        
        Args:
            milvus_connection_id (int): Milvus连接配置ID
        """
        self.milvus_connection_id = milvus_connection_id
        self.embedding_service = get_embedding_service()
        self.milvus_connector = None
        
    def __enter__(self):
        """同步上下文管理器入口"""
        self._connect_to_milvus()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """同步上下文管理器出口"""
        self._disconnect_from_milvus()
        
    def _connect_to_milvus(self):
        """连接到Milvus数据库"""
        try:
            logger.info(f"尝试连接Milvus，连接ID: {self.milvus_connection_id}")
            connection = MulvesConnection.objects.get(
                id=self.milvus_connection_id, 
                is_active=True
            )
            logger.info(f"获取到连接配置: {connection.name}")
            self.milvus_connector = MulvesDBConnector(connection)
            logger.info("创建MulvesDBConnector实例成功")
            self.milvus_connector.connect_sync()
            logger.info(f"成功连接到Milvus: {connection.name}")
        except Exception as e:
            logger.error(f"连接Milvus失败: {str(e)}")
            logger.exception("详细错误信息:")
            raise ConnectionError(f"无法连接到Milvus数据库: {str(e)}")
            
    def _disconnect_from_milvus(self):
        """断开Milvus连接"""
        if self.milvus_connector:
            self.milvus_connector.disconnect_sync()
            self.milvus_connector = None


class PDFVectorStorageServiceWithConnector:
    """使用已有连接器的PDF向量存储服务"""
    
    def __init__(self, milvus_connector: MulvesDBConnector):
        """
        初始化向量存储服务（使用已有连接器）
        
        Args:
            milvus_connector (MulvesDBConnector): 已建立的Milvus连接器
        """
        self.milvus_connector = milvus_connector
        self.embedding_service = get_embedding_service()
        
    def __enter__(self):
        """同步上下文管理器入口 - 不需要重新连接"""
        logger.info("使用已建立的Milvus连接器")
        # 验证连接是否有效
        if not self.milvus_connector._milvus_client:
            raise ConnectionError("提供的Milvus连接器未连接")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """同步上下文管理器出口 - 不主动断开连接（由调用方负责）"""
        logger.info("退出PDFVectorStorageServiceWithConnector上下文")
        # 不主动断开连接，因为连接是由外部管理的
        pass
        
    def create_document_collection(self, collection_name: str) -> bool:
        """
        创建文档向量集合
        
        Args:
            collection_name (str): 集合名称
            
        Returns:
            bool: 创建是否成功
        """
        if not self.milvus_connector:
            raise ConnectionError("未连接到Milvus")
            
        # 定义集合schema
        schema = {
            "fields": [
                {
                    "name": "id",
                    "type": "INT64",
                    "is_primary": True,
                    "auto_id": True
                },
                {
                    "name": "vector_id",
                    "type": "VARCHAR",
                    "max_length": 100
                },
                {
                    "name": "content",
                    "type": "VARCHAR",
                    "max_length": 65535
                },
                {
                    "name": "embedding",
                    "type": "FLOAT_VECTOR",
                    "dim": self.embedding_service.get_embedding_dimensions()
                },
                {
                    "name": "page_number",
                    "type": "INT64"
                },
                {
                    "name": "chunk_index",
                    "type": "INT64"
                },
                {
                    "name": "document_id",
                    "type": "INT64"
                },
                {
                    "name": "metadata",
                    "type": "JSON"
                }
            ],
            "description": "PDF文档向量存储集合"
        }
        
        try:
            self.milvus_connector.create_milvus_collection_sync(collection_name, schema)
            logger.info(f"成功创建集合: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"创建集合失败: {str(e)}")
            raise
    
    def store_pdf_chunks(self, document_id: int, chunks_data: List[Dict], 
                        collection_name: str) -> Dict[str, Any]:
        """
        存储PDF分块向量到Milvus
        
        Args:
            document_id (int): PDF文档ID
            chunks_data (List[Dict]): 分块数据列表
            collection_name (str): 集合名称
            
        Returns:
            Dict[str, Any]: 存储结果
        """
        if not self.milvus_connector:
            raise ConnectionError("未连接到Milvus")
            
        try:
            # 1. 生成embedding
            texts = [chunk['content'] for chunk in chunks_data]
            logger.info(f"开始生成 {len(texts)} 个文本的embedding")
            
            embeddings = self.embedding_service.embed_batch(texts)
            logger.info(f"完成embedding生成")
            
            # 2. 准备Milvus数据
            milvus_data = []
            successful_chunks = []
            
            for i, (chunk_data, embedding_result) in enumerate(zip(chunks_data, embeddings)):
                if not embedding_result.metadata.get('failed', False):
                    vector_id = str(uuid.uuid4())
                    
                    milvus_record = {
                        "vector_id": vector_id,
                        "content": chunk_data['content'],
                        "embedding": embedding_result.embedding,
                        "page_number": chunk_data['page_number'],
                        "chunk_index": chunk_data['chunk_index'],
                        "document_id": document_id,
                        "metadata": chunk_data.get('metadata', {})
                    }
                    
                    milvus_data.append(milvus_record)
                    successful_chunks.append({
                        'chunk_index': chunk_data['chunk_index'],
                        'vector_id': vector_id,
                        'embedding_result': embedding_result
                    })
                else:
                    logger.warning(f"跳过第 {chunk_data['chunk_index']} 个分块（embedding失败）")
            
            if not milvus_data:
                raise Exception("所有分块的embedding都失败了")
            
            # 3. 写入Milvus（启用去重）
            logger.info(f"开始写入 {len(milvus_data)} 条记录到Milvus（启用去重）")
            result = self.milvus_connector.insert_milvus_data_sync(
                collection_name=collection_name,
                data=milvus_data,
                enable_dedup=True,
                document_id=document_id
            )
            
            # 4. 更新本地数据库记录
            self._update_chunk_records(document_id, successful_chunks)
            
            # 5. 计算元数据追踪数量（基于成功存储的分块数）
            metadata_tracked = len(successful_chunks)
            
            logger.info(f"成功存储 {len(successful_chunks)} 个分块向量，追踪 {metadata_tracked} 条元数据")
            
            return {
                'success': True,
                'stored_count': len(successful_chunks),
                'total_chunks': len(chunks_data),
                'failed_count': len(chunks_data) - len(successful_chunks),
                'metadata_tracked': metadata_tracked,
                'details': result
            }
            
        except Exception as e:
            logger.error(f"存储PDF分块失败: {str(e)}")
            raise
    
    def _update_chunk_records(self, document_id: int, successful_chunks: List[Dict]):
        """更新本地分块记录"""
        try:
            with transaction.atomic():
                # 创建分块记录
                chunk_objects = [
                    PDFChunk(
                        document_id=document_id,
                        chunk_index=chunk['chunk_index'],
                        vector_id=chunk['vector_id'],
                        # embedding_model=self.embedding_service.get_model_name(),
                        # embedding_provider=self.embedding_service.get_provider_name()
                    )
                    for chunk in successful_chunks
                ]
                PDFChunk.objects.bulk_create(chunk_objects)
                logger.info(f"创建了 {len(chunk_objects)} 个本地分块记录")
        except Exception as e:
            logger.error(f"更新本地分块记录失败: {str(e)}")
            # 不抛出异常，因为这不影响主要的向量存储
    
    def search_similar_chunks_sync(self, collection_name: str, query_text: str, 
                                 limit: int = 10) -> List[Dict]:
        """
        同步向量相似度搜索
        
        Args:
            collection_name (str): 集合名称
            query_text (str): 查询文本
            limit (int): 返回结果数量限制
            
        Returns:
            List[Dict]: 搜索结果
        """
        if not self.milvus_connector:
            raise ConnectionError("未连接到Milvus")
            
        try:
            # 生成查询文本的embedding
            embedding_result = self.embedding_service.embed_text(query_text)
            if embedding_result.metadata.get('failed', False):
                raise Exception("查询文本embedding生成失败")
            
            query_vector = embedding_result.embedding
            
            # 执行向量搜索
            search_result = self.milvus_connector._milvus_client.search(
                collection_name=collection_name,
                data=[query_vector],
                anns_field="embedding",
                search_params={"metric_type": "L2", "params": {"nprobe": 10}},
                limit=limit,
                output_fields=["content", "page_number", "chunk_index", "metadata"]
            )
            
            # 格式化结果
            formatted_results = []
            if search_result and len(search_result) > 0:
                for item in search_result[0]:
                    formatted_results.append({
                        'id': item.get('id'),
                        'content': item.get('content', ''),
                        'distance': item.get('distance', 0),
                        'similarity': 1.0 - (item.get('distance', 0) / 2.0),
                        'page_number': item.get('page_number', 1),
                        'chunk_index': item.get('chunk_index', 0),
                        'metadata': item.get('metadata', {})
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            raise
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        获取集合信息
        
        Args:
            collection_name (str): 集合名称
            
        Returns:
            Dict[str, Any]: 集合信息
        """
        if not self.milvus_connector:
            raise ConnectionError("未连接到Milvus")
            
        try:
            collections_info = self.milvus_connector.get_milvus_collections_info_sync()
            for info in collections_info:
                if info['name'] == collection_name:
                    # 确保返回的对象包含exists字段
                    info['exists'] = True
                    return info
            return {'name': collection_name, 'exists': False}
        except Exception as e:
            logger.error(f"获取集合信息失败: {str(e)}")
            raise


class PDFProcessingPipeline:
    """PDF处理流水线"""
    
    def __init__(self, milvus_connection_id: int, milvus_connector=None):
        logger.info(f"初始化PDFProcessingPipeline，连接ID: {milvus_connection_id}")
        self.milvus_connection_id = milvus_connection_id
        if milvus_connector:
            # 使用已有的连接器
            logger.info("使用传入的Milvus连接器")
            self.vector_storage_service = PDFVectorStorageServiceWithConnector(milvus_connector)
        else:
            # 使用传统的连接方式
            logger.info("使用传统Milvus连接方式")
            self.vector_storage_service = PDFVectorStorageService(milvus_connection_id)
        
    def process_pdf_document(self, pdf_document: PDFDocument, file_path: str, use_existing_collection: bool = True) -> Dict[str, Any]:
        """
        完整的PDF文档处理流程
        
        Args:
            pdf_document (PDFDocument): PDF文档对象
            file_path (str): PDF文件路径
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        from .pdf_processor import PDFProcessor
        
        try:
            # 标记为处理中
            pdf_document.mark_as_processing()
            logger.info("文档状态已标记为处理中")
            
            # 1. 检查或创建Milvus集合（在上下文管理器中）
            logger.info(f"开始处理Milvus集合: {pdf_document.collection_name}")
            with self.vector_storage_service as storage_service:
                if use_existing_collection:
                    # 检查集合是否已存在
                    collection_exists = False
                    try:
                        collections_info = storage_service.get_collection_info(pdf_document.collection_name)
                        collection_exists = collections_info.get('exists', False)
                        if collection_exists:
                            logger.info(f"使用现有集合: {pdf_document.collection_name}")
                        else:
                            logger.info(f"集合 {pdf_document.collection_name} 不存在")
                    except Exception as e:
                        logger.warning(f"检查集合时出错: {str(e)}，将尝试创建集合")
                        collection_exists = False
                    
                    # 如果集合不存在，创建它
                    if not collection_exists:
                        try:
                            logger.info(f"创建集合: {pdf_document.collection_name}")
                            storage_service.create_document_collection(pdf_document.collection_name)
                        except Exception as e:
                            logger.error(f"创建集合失败: {str(e)}")
                            raise
                else:
                    # 保持原来的动态创建行为
                    storage_service.create_document_collection(pdf_document.collection_name)
                logger.info("Milvus集合处理完成")
                
                # 2. 处理PDF文件
                processor = PDFProcessor()
                chunks_data = list(processor.process_pdf(file_path))
                
                if not chunks_data:
                    raise ValueError("PDF文件处理后没有生成任何有效分块")
                
                # 3. 存储向量
                result = storage_service.store_pdf_chunks(
                    document_id=pdf_document.id,
                    chunks_data=[{
                        'content': chunk.content,
                        'page_number': chunk.page_number,
                        'chunk_index': chunk.chunk_index,
                        'metadata': chunk.metadata
                    } for chunk in chunks_data],
                    collection_name=pdf_document.collection_name
                )
            
            # 4. 标记为完成
            pdf_document.mark_as_completed()
            
            return {
                'success': True,
                'document_id': pdf_document.id,
                'chunks_processed': len(chunks_data),
                'chunks_stored': result['stored_count'],
                'storage_result': result
            }
            
        except Exception as e:
            # 标记为失败
            pdf_document.mark_as_failed(str(e))
            logger.error(f"PDF文档处理失败: {str(e)}")
            raise