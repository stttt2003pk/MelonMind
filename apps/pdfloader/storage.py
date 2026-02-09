import logging
import uuid
from typing import List, Dict, Any
from datetime import datetime
from django.db import transaction
from apps.mulvesdb.connectors import MulvesDBConnector
from apps.mulvesdb.models import MulvesConnection
from .models import PDFDocument, PDFChunk
from .embedding import get_embedding_service, EmbeddingResult

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
            connection = MulvesConnection.objects.get(
                id=self.milvus_connection_id, 
                is_active=True
            )
            self.milvus_connector = MulvesDBConnector(connection)
            self.milvus_connector.connect_sync()
            logger.info(f"成功连接到Milvus: {connection.name}")
        except Exception as e:
            logger.error(f"连接Milvus失败: {str(e)}")
            raise ConnectionError(f"无法连接到Milvus数据库: {str(e)}")
            
    def _disconnect_from_milvus(self):
        """断开Milvus连接"""
        if self.milvus_connector:
            self.milvus_connector.disconnect_sync()
            self.milvus_connector = None
            
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
                'milvus_result': result,
                'metadata_tracked': metadata_tracked
            }
            
        except Exception as e:
            logger.error(f"存储PDF分块失败: {str(e)}")
            raise
    
    def _update_chunk_records(self, document_id: int, successful_chunks: List[Dict]):
        """
        更新本地chunk记录
        
        Args:
            document_id (int): 文档ID
            successful_chunks (List[Dict]): 成功处理的分块数据
        """
        try:
            with transaction.atomic():
                document = PDFDocument.objects.select_for_update().get(id=document_id)
                
                for chunk_info in successful_chunks:
                    PDFChunk.objects.create(
                        document=document,
                        chunk_index=chunk_info['chunk_index'],
                        content=chunk_info['embedding_result'].text,
                        page_number=chunk_info['embedding_result'].metadata.get('page_number', 0),
                        vector_id=chunk_info['vector_id'],
                        embedding_model='qwen',
                        metadata=chunk_info['embedding_result'].metadata
                    )
                    
        except Exception as e:
            logger.error(f"更新chunk记录失败: {str(e)}")
            raise
    
    def search_similar_chunks(self, collection_name: str, query_text: str, 
                             limit: int = 10) -> List[Dict]:
        """
        搜索相似的文档分块
        
        Args:
            collection_name (str): 集合名称
            query_text (str): 查询文本
            limit (int): 返回结果数量
            
        Returns:
            List[Dict]: 相似分块列表
        """
        if not self.milvus_connector:
            raise ConnectionError("未连接到Milvus")
            
        try:
            # 生成查询文本的embedding
            query_embedding = self.embedding_service.embed_text(query_text)
            
            # 在Milvus中搜索
            raw_results = self.milvus_connector.execute_milvus_vector_search_sync(
                collection_name=collection_name,
                vector_field="embedding",
                query_vector=query_embedding.embedding,
                limit=limit
            )
            
            # 转换Milvus结果为标准格式
            formatted_results = []
            if raw_results and len(raw_results) > 0:
                # Milvus搜索结果通常是嵌套的列表
                search_result = raw_results[0] if isinstance(raw_results, list) else raw_results
                
                # 处理搜索结果中的实体
                if hasattr(search_result, 'entities'):
                    entities = search_result.entities
                    for i, entity in enumerate(entities[:limit]):
                        formatted_results.append({
                            'id': entity.get('vector_id', f'vector_{i}'),
                            'content': entity.get('content', ''),
                            'similarity': 1.0 - (entity.get('distance', 0) / 2.0),  # 转换距离为相似度
                            'page_number': entity.get('page_number', 1),
                            'chunk_index': entity.get('chunk_index', 0),
                            'metadata': entity.get('metadata', {})
                        })
                else:
                    # 如果是字典格式，直接处理
                    if isinstance(search_result, list):
                        for i, item in enumerate(search_result[:limit]):
                            formatted_results.append({
                                'id': item.get('vector_id', f'vector_{i}'),
                                'content': item.get('content', ''),
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
                    return info
            return {'name': collection_name, 'exists': False}
        except Exception as e:
            logger.error(f"获取集合信息失败: {str(e)}")
            raise


class PDFProcessingPipeline:
    """PDF处理流水线"""
    
    def __init__(self, milvus_connection_id: int):
        self.milvus_connection_id = milvus_connection_id
        self.vector_storage_service = PDFVectorStorageService(milvus_connection_id)
        
    def process_pdf_document(self, pdf_document: PDFDocument, file_path: str) -> Dict[str, Any]:
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
            
            # 1. 创建Milvus集合
            self.vector_storage_service.create_document_collection(pdf_document.collection_name)
            
            # 2. 处理PDF文件
            processor = PDFProcessor()
            chunks_data = list(processor.process_pdf(file_path))
            
            if not chunks_data:
                raise ValueError("PDF文件处理后没有生成任何有效分块")
            
            # 3. 存储向量
            with self.vector_storage_service as storage_service:
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