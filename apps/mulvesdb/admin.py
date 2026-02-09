from django.contrib import admin
from .models import MulvesConnection, MulvesQueryLog, MulvesDataCache, VectorMetadata


@admin.register(MulvesConnection)
class MulvesConnectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'host', 'port', 'database', 'is_active', 'created_at']
    list_filter = ['is_active', 'ssl_enabled', 'created_at']
    search_fields = ['name', 'host', 'database']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'host', 'port', 'database')
        }),
        ('认证信息', {
            'fields': ('username', 'password')
        }),
        ('连接配置', {
            'fields': ('ssl_enabled', 'connection_timeout')
        }),
        ('状态', {
            'fields': ('is_active',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MulvesQueryLog)
class MulvesQueryLogAdmin(admin.ModelAdmin):
    list_display = ['connection', 'execution_time', 'result_count', 'created_at']
    list_filter = ['created_at', 'connection']
    search_fields = ['query_sql', 'connection__name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('查询信息', {
            'fields': ('connection', 'query_sql')
        }),
        ('执行结果', {
            'fields': ('execution_time', 'result_count', 'error_message')
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(MulvesDataCache)
class MulvesDataCacheAdmin(admin.ModelAdmin):
    list_display = ['cache_key', 'expires_at', 'created_at', 'is_expired']
    list_filter = ['expires_at', 'created_at']
    search_fields = ['cache_key']
    readonly_fields = ['created_at', 'updated_at', 'is_expired']
    
    fieldsets = (
        ('缓存信息', {
            'fields': ('cache_key', 'data')
        }),
        ('有效期', {
            'fields': ('expires_at',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at', 'is_expired'),
            'classes': ('collapse',)
        }),
    )


@admin.register(VectorMetadata)
class VectorMetadataAdmin(admin.ModelAdmin):
    list_display = ['vector_id_short', 'collection_name', 'source_document_id', 
                   'source_chunk_index', 'embedding_model', 'status', 'created_at']
    list_filter = ['status', 'collection_name', 'embedding_model', 'document_category', 
                  'importance_level', 'created_at']
    search_fields = ['vector_id', 'collection_name', 'content_preview', 'document_category']
    readonly_fields = ['created_at', 'updated_at', 'last_accessed']
    date_hierarchy = 'created_at'
    
    # 自定义显示方法
    def vector_id_short(self, obj):
        return obj.vector_id[:12] + '...' if len(obj.vector_id) > 12 else obj.vector_id
    vector_id_short.short_description = '向量ID'
    
    actions = ['archive_selected', 'soft_delete_selected', 'cleanup_old_metadata']
    
    fieldsets = (
        ('向量信息', {
            'fields': ('vector_id', 'collection_name')
        }),
        ('来源信息', {
            'fields': ('source_document_id', 'source_chunk_index', 'source_app')
        }),
        ('技术信息', {
            'fields': ('embedding_model', 'embedding_dimensions', 'processing_time_ms')
        }),
        ('内容信息', {
            'fields': ('content_length', 'page_number', 'content_preview')
        }),
        ('业务信息', {
            'fields': ('document_category', 'tags', 'importance_level')
        }),
        ('管理信息', {
            'fields': ('created_by', 'status')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at', 'last_accessed'),
            'classes': ('collapse',)
        }),
    )
    
    def archive_selected(self, request, queryset):
        """批量归档选中的元数据"""
        count = queryset.count()
        queryset.update(status='archived')
        self.message_user(request, f'成功归档 {count} 条元数据记录')
    archive_selected.short_description = '归档选中的元数据'
    
    def soft_delete_selected(self, request, queryset):
        """批量软删除选中的元数据"""
        count = queryset.count()
        queryset.update(status='deleted')
        self.message_user(request, f'成功软删除 {count} 条元数据记录')
    soft_delete_selected.short_description = '软删除选中的元数据'
    
    def cleanup_old_metadata(self, request, queryset):
        """清理旧的元数据（超过90天）"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=90)
        old_metadata = VectorMetadata.objects.filter(created_at__lt=cutoff_date)
        count = old_metadata.count()
        old_metadata.delete()
        self.message_user(request, f'成功清理 {count} 条超过90天的元数据记录')
    cleanup_old_metadata.short_description = '清理90天前的元数据'