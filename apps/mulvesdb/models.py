from django.db import models
from django.utils import timezone
from typing import List, Set, Optional
import logging


class MulvesConnection(models.Model):
    """Mulves数据库连接配置"""
    name = models.CharField(max_length=100, unique=True, verbose_name='连接名称')
    host = models.CharField(max_length=255, verbose_name='主机地址')
    port = models.IntegerField(default=5432, verbose_name='端口号')
    database = models.CharField(max_length=100, verbose_name='数据库名')
    username = models.CharField(max_length=100, verbose_name='用户名')
    password = models.CharField(max_length=255, verbose_name='密码')
    ssl_enabled = models.BooleanField(default=False, verbose_name='SSL启用')
    connection_timeout = models.IntegerField(default=30, verbose_name='连接超时(秒)')
    
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'mulves_connections'
        verbose_name = 'Mulves连接配置'
        verbose_name_plural = 'Mulves连接配置'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.host}:{self.port}/{self.database})"


class MulvesQueryLog(models.Model):
    """Mulves查询日志"""
    connection = models.ForeignKey(
        MulvesConnection, 
        on_delete=models.CASCADE, 
        related_name='query_logs',
        verbose_name='连接配置'
    )
    query_sql = models.TextField(verbose_name='SQL查询语句')
    execution_time = models.FloatField(verbose_name='执行时间(毫秒)')
    result_count = models.IntegerField(null=True, blank=True, verbose_name='结果数量')
    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='执行时间')

    class Meta:
        db_table = 'mulves_query_logs'
        verbose_name = 'Mulves查询日志'
        verbose_name_plural = 'Mulves查询日志'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['connection', 'created_at']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Query on {self.connection.name} at {self.created_at}"


class MulvesDataCache(models.Model):
    """Mulves数据缓存"""
    cache_key = models.CharField(max_length=255, unique=True, verbose_name='缓存键')
    data = models.JSONField(verbose_name='缓存数据')
    expires_at = models.DateTimeField(verbose_name='过期时间')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'mulves_data_cache'
        verbose_name = 'Mulves数据缓存'
        verbose_name_plural = 'Mulves数据缓存'
        indexes = [
            models.Index(fields=['cache_key']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Cache: {self.cache_key}"

    @property
    def is_expired(self):
        """检查缓存是否已过期"""
        if self.expires_at is None:
            return True
        return timezone.now() > self.expires_at
        
    def clean_expired_cache(self):
        """清理过期的缓存记录（同步方法）"""
        expired_caches = MulvesDataCache.objects.filter(expires_at__lt=timezone.now())
        count = expired_caches.count()
        expired_caches.delete()
        return count


class ChunkHashIndex(models.Model):
    """块级哈希索引，用于去重"""
    
    # 哈希值相关
    hash_value = models.CharField(max_length=64, verbose_name='块哈希值')
    content_length = models.IntegerField(verbose_name='内容长度')
    
    # 关联信息
    collection_name = models.CharField(max_length=100, verbose_name='集合名称')
    document_id = models.IntegerField(verbose_name='文档ID')
    chunk_index = models.IntegerField(verbose_name='块索引')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    last_accessed = models.DateTimeField(auto_now=True, verbose_name='最后访问时间')
    
    class Meta:
        db_table = 'chunk_hash_indices'
        verbose_name = '块哈希索引'
        verbose_name_plural = '块哈希索引'
        unique_together = ['hash_value', 'collection_name']  # 同一集合内哈希唯一
        indexes = [
            models.Index(fields=['hash_value']),
            models.Index(fields=['collection_name']),
            models.Index(fields=['document_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Hash:{self.hash_value[:8]}... Doc:{self.document_id} Chunk:{self.chunk_index}"
    
    @classmethod
    def is_duplicate(cls, hash_value: str, collection_name: str) -> bool:
        """检查指定集合中是否存在相同的哈希值"""
        return cls.objects.filter(
            hash_value=hash_value,
            collection_name=collection_name
        ).exists()
    
    @classmethod
    def add_hash_entry(cls, hash_value: str, collection_name: str, 
                      document_id: int, chunk_index: int, content_length: int) -> bool:
        """添加哈希索引记录"""
        try:
            obj, created = cls.objects.get_or_create(
                hash_value=hash_value,
                collection_name=collection_name,
                defaults={
                    'document_id': document_id,
                    'chunk_index': chunk_index,
                    'content_length': content_length
                }
            )
            return created  # True表示新建，False表示已存在
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"添加哈希索引失败: {str(e)}")
            return False
    
    @classmethod
    def bulk_check_duplicates(cls, hash_values: List[str], collection_name: str) -> Set[str]:
        """批量检查重复哈希值"""
        existing_hashes = cls.objects.filter(
            hash_value__in=hash_values,
            collection_name=collection_name
        ).values_list('hash_value', flat=True)
        return set(existing_hashes)
    
    @classmethod
    def cleanup_old_entries(cls, days_old: int = 30):
        """清理旧的哈希索引记录"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days_old)
        deleted_count, _ = cls.objects.filter(created_at__lt=cutoff_date).delete()
        return deleted_count


class VectorMetadata(models.Model):
    """向量元数据追踪模型"""
    
    # 向量标识
    vector_id = models.CharField(max_length=100, verbose_name='向量ID')
    collection_name = models.CharField(max_length=100, verbose_name='集合名称')
    
    # 来源追踪
    source_document_id = models.IntegerField(verbose_name='源文档ID')
    source_chunk_index = models.IntegerField(verbose_name='源分块索引')
    source_app = models.CharField(max_length=50, default='pdfloader', verbose_name='源应用')
    
    # 技术信息
    embedding_model = models.CharField(max_length=100, verbose_name='嵌入模型')
    embedding_dimensions = models.IntegerField(verbose_name='嵌入维度')
    processing_time_ms = models.FloatField(null=True, blank=True, verbose_name='处理耗时(毫秒)')
    
    # 内容信息
    content_length = models.IntegerField(verbose_name='内容长度')
    page_number = models.IntegerField(null=True, blank=True, verbose_name='页码')
    content_preview = models.CharField(max_length=500, verbose_name='内容预览')
    
    # 业务信息
    document_category = models.CharField(max_length=50, blank=True, verbose_name='文档分类')
    tags = models.JSONField(default=list, verbose_name='标签')
    importance_level = models.IntegerField(default=1, verbose_name='重要性等级')  # 1-5级
    
    # 管理信息
    created_by = models.CharField(max_length=100, blank=True, verbose_name='创建者')
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', '活跃'),
            ('archived', '已归档'),
            ('deleted', '已删除'),
        ],
        default='active',
        verbose_name='状态'
    )
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    last_accessed = models.DateTimeField(null=True, blank=True, verbose_name='最后访问时间')
    
    class Meta:
        db_table = 'vector_metadata'
        verbose_name = '向量元数据'
        verbose_name_plural = '向量元数据'
        unique_together = ['vector_id', 'collection_name']
        indexes = [
            models.Index(fields=['source_document_id']),
            models.Index(fields=['collection_name']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['document_category']),
            models.Index(fields=['importance_level']),
        ]
    
    def __str__(self):
        return f"Vector:{self.vector_id[:8]}... Doc:{self.source_document_id} Chunk:{self.source_chunk_index}"
    
    @classmethod
    def create_metadata(cls, vector_id: str, collection_name: str, 
                       source_document_id: int, source_chunk_index: int,
                       embedding_model: str, embedding_dimensions: int,
                       content: str, page_number: Optional[int] = None,
                       processing_time_ms: Optional[float] = None,
                       **kwargs) -> 'VectorMetadata':
        """创建向量元数据记录"""
        try:
            metadata = cls.objects.create(
                vector_id=vector_id,
                collection_name=collection_name,
                source_document_id=source_document_id,
                source_chunk_index=source_chunk_index,
                source_app=kwargs.get('source_app', 'pdfloader'),
                embedding_model=embedding_model,
                embedding_dimensions=embedding_dimensions,
                processing_time_ms=processing_time_ms,
                content_length=len(content),
                page_number=page_number,
                content_preview=content[:500],
                document_category=kwargs.get('document_category', ''),
                tags=kwargs.get('tags', []),
                importance_level=kwargs.get('importance_level', 1),
                created_by=kwargs.get('created_by', '')
            )
            return metadata
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"创建向量元数据失败: {str(e)}")
            raise
    
    @classmethod
    def get_metadata_by_vector(cls, vector_id: str, collection_name: str) -> Optional['VectorMetadata']:
        """根据向量ID获取元数据"""
        try:
            return cls.objects.get(vector_id=vector_id, collection_name=collection_name)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_metadata_by_document(cls, document_id: int, collection_name: str) -> List['VectorMetadata']:
        """根据文档ID获取所有相关元数据"""
        return list(cls.objects.filter(
            source_document_id=document_id,
            collection_name=collection_name
        ))
    
    @classmethod
    def bulk_get_metadata(cls, vector_ids: List[str], collection_name: str) -> List['VectorMetadata']:
        """批量获取元数据"""
        return list(cls.objects.filter(
            vector_id__in=vector_ids,
            collection_name=collection_name
        ))
    
    @classmethod
    def update_access_time(cls, vector_id: str, collection_name: str):
        """更新最后访问时间"""
        try:
            cls.objects.filter(
                vector_id=vector_id,
                collection_name=collection_name
            ).update(last_accessed=timezone.now())
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"更新访问时间失败: {str(e)}")
    
    @classmethod
    def cleanup_old_metadata(cls, days_old: int = 90):
        """清理旧的元数据记录"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days_old)
        deleted_count, _ = cls.objects.filter(created_at__lt=cutoff_date).delete()
        return deleted_count
    
    def archive(self):
        """归档元数据"""
        self.status = 'archived'
        self.save(update_fields=['status'])
    
    def soft_delete(self):
        """软删除元数据"""
        self.status = 'deleted'
        self.save(update_fields=['status'])