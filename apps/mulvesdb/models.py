from django.db import models
from django.utils import timezone


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