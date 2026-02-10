from django.db import models
from django.utils import timezone
from apps.mulvesdb.models import MulvesConnection


class PDFDocument(models.Model):
    """PDF文档元数据"""
    title = models.CharField(max_length=500, verbose_name='文档标题')
    file_path = models.CharField(max_length=1000, verbose_name='文件路径')
    file_size = models.BigIntegerField(verbose_name='文件大小(字节)')
    file_hash = models.CharField(max_length=64, blank=True, null=True, verbose_name='文件哈希值')
    page_count = models.IntegerField(verbose_name='页数')
    
    # 文档处理状态
    STATUS_CHOICES = [
        ('uploaded', '已上传'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '处理失败'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded', verbose_name='处理状态')
    
    # 关联的Milvus连接
    milvus_connection = models.ForeignKey(
        MulvesConnection,
        on_delete=models.CASCADE,
        related_name='pdf_documents',
        verbose_name='Milvus连接'
    )
    
    # 集合名称（在Milvus中）
    collection_name = models.CharField(max_length=100, verbose_name='Milvus集合名称')
    
    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    processed_at = models.DateTimeField(blank=True, null=True, verbose_name='处理完成时间')

    class Meta:
        db_table = 'pdf_documents'
        verbose_name = 'PDF文档'
        verbose_name_plural = 'PDF文档'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['milvus_connection']),
            models.Index(fields=['file_hash']),
        ]

    def __str__(self):
        return f"{self.title} ({self.file_path})"

    def mark_as_processing(self):
        """标记为处理中"""
        self.status = 'processing'
        self.save(update_fields=['status'])

    def mark_as_completed(self):
        """标记为处理完成"""
        self.status = 'completed'
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])

    def mark_as_failed(self, error_message):
        """标记为处理失败"""
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])
    
    @classmethod
    def get_by_file_hash(cls, file_hash):
        """根据文件哈希值查找文档"""
        try:
            return cls.objects.get(file_hash=file_hash)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def exists_by_file_hash(cls, file_hash):
        """检查是否存在具有相同哈希值的文档"""
        return cls.objects.filter(file_hash=file_hash).exists()


class PDFCollectionConfig(models.Model):
    """PDF文档集合配置"""
    
    name = models.CharField(max_length=100, unique=True, verbose_name='集合名称')
    description = models.TextField(blank=True, verbose_name='描述')
    
    # 关联的Milvus连接
    milvus_connection = models.ForeignKey(
        MulvesConnection,
        on_delete=models.CASCADE,
        related_name='pdf_collection_configs',
        verbose_name='Milvus连接'
    )
    
    # 集合在Milvus中的实际名称
    milvus_collection_name = models.CharField(max_length=100, verbose_name='Milvus集合名称')
    
    # 状态管理
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    is_default = models.BooleanField(default=False, verbose_name='是否默认集合')
    
    # 配置信息
    config_data = models.JSONField(default=dict, blank=True, verbose_name='配置数据')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'pdf_collection_configs'
        verbose_name = 'PDF集合配置'
        verbose_name_plural = 'PDF集合配置'
        ordering = ['-is_default', '-created_at']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['is_default']),
            models.Index(fields=['milvus_connection']),
        ]

    def __str__(self):
        return f"{self.name} ({self.milvus_collection_name})"
    
    @classmethod
    def get_default_collection(cls, milvus_connection_id=None):
        """获取默认集合配置"""
        try:
            if milvus_connection_id:
                return cls.objects.get(
                    is_default=True, 
                    is_active=True,
                    milvus_connection_id=milvus_connection_id
                )
            else:
                return cls.objects.get(is_default=True, is_active=True)
        except cls.DoesNotExist:
            # 如果没有默认配置，返回第一个激活的配置
            try:
                if milvus_connection_id:
                    return cls.objects.filter(
                        is_active=True,
                        milvus_connection_id=milvus_connection_id
                    ).first()
                else:
                    return cls.objects.filter(is_active=True).first()
            except cls.DoesNotExist:
                return None
    
    @classmethod
    def collection_exists(cls, collection_name):
        """检查集合配置是否存在"""
        return cls.objects.filter(
            milvus_collection_name=collection_name,
            is_active=True
        ).exists()
    
    @classmethod
    def get_collection_by_name(cls, name):
        """根据名称获取集合配置"""
        try:
            return cls.objects.get(name=name, is_active=True)
        except cls.DoesNotExist:
            return None


class PDFChunk(models.Model):
    """PDF文档分块数据"""
    document = models.ForeignKey(
        PDFDocument,
        on_delete=models.CASCADE,
        related_name='chunks',
        verbose_name='所属文档'
    )
    
    # 分块内容
    chunk_index = models.IntegerField(verbose_name='分块索引')
    content = models.TextField(verbose_name='分块内容')
    page_number = models.IntegerField(verbose_name='所在页码')
    
    # 向量相关
    vector_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='向量ID')
    embedding_model = models.CharField(max_length=100, default='qwen', verbose_name='嵌入模型')
    
    # 元数据
    metadata = models.JSONField(default=dict, verbose_name='元数据')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'pdf_chunks'
        verbose_name = 'PDF分块'
        verbose_name_plural = 'PDF分块'
        ordering = ['document', 'chunk_index']
        indexes = [
            models.Index(fields=['document', 'chunk_index']),
            models.Index(fields=['vector_id']),
        ]

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.title}"