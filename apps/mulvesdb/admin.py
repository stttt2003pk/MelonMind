from django.contrib import admin
from .models import MulvesConnection, MulvesQueryLog, MulvesDataCache


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