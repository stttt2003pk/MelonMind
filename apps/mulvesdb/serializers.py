from rest_framework import serializers
from .models import MulvesConnection, MulvesQueryLog, MulvesDataCache


class MulvesConnectionSerializer(serializers.ModelSerializer):
    """Mulves连接配置序列化器"""
    
    class Meta:
        model = MulvesConnection
        fields = [
            'id', 'name', 'host', 'port', 'database', 'username',
            'ssl_enabled', 'connection_timeout', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_port(self, value):
        """验证端口号范围"""
        if not 1 <= value <= 65535:
            raise serializers.ValidationError("端口号必须在1-65535之间")
        return value

    def validate_connection_timeout(self, value):
        """验证连接超时时间"""
        if value <= 0:
            raise serializers.ValidationError("连接超时时间必须大于0")
        return value


class MulvesConnectionDetailSerializer(MulvesConnectionSerializer):
    """Mulves连接配置详细序列化器（包含统计信息）"""
    query_count = serializers.SerializerMethodField()
    last_query_time = serializers.SerializerMethodField()

    class Meta(MulvesConnectionSerializer.Meta):
        fields = MulvesConnectionSerializer.Meta.fields + [
            'query_count', 'last_query_time'
        ]

    def get_query_count(self, obj):
        """获取查询次数"""
        return obj.query_logs.count()

    def get_last_query_time(self, obj):
        """获取最后查询时间"""
        last_log = obj.query_logs.order_by('-created_at').first()
        return last_log.created_at if last_log else None


class MulvesQueryLogSerializer(serializers.ModelSerializer):
    """Mulves查询日志序列化器"""
    connection_name = serializers.CharField(source='connection.name', read_only=True)

    class Meta:
        model = MulvesQueryLog
        fields = [
            'id', 'connection', 'connection_name', 'query_sql',
            'execution_time', 'result_count', 'error_message', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class MulvesDataCacheSerializer(serializers.ModelSerializer):
    """Mulves数据缓存序列化器"""
    is_expired = serializers.ReadOnlyField()

    class Meta:
        model = MulvesDataCache
        fields = [
            'id', 'cache_key', 'data', 'expires_at',
            'created_at', 'updated_at', 'is_expired'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_expired']

    def validate_expires_at(self, value):
        """验证过期时间"""
        from django.utils import timezone
        if value <= timezone.now():
            raise serializers.ValidationError("过期时间必须晚于当前时间")
        return value


class MulvesQueryRequestSerializer(serializers.Serializer):
    """Mulves查询请求序列化器"""
    connection_id = serializers.IntegerField(required=True, help_text='连接配置ID')
    query_sql = serializers.CharField(required=True, help_text='SQL查询语句')
    use_cache = serializers.BooleanField(default=True, help_text='是否使用缓存')
    cache_timeout = serializers.IntegerField(
        default=300, 
        min_value=1, 
        max_value=3600,
        help_text='缓存超时时间(秒)'
    )


class MulvesTestConnectionSerializer(serializers.Serializer):
    """Mulves连接测试序列化器"""
    host = serializers.CharField(required=True, help_text='主机地址')
    port = serializers.IntegerField(
        required=True, 
        min_value=1, 
        max_value=65535,
        help_text='端口号'
    )
    database = serializers.CharField(required=True, help_text='数据库名')
    username = serializers.CharField(required=True, help_text='用户名')
    password = serializers.CharField(required=True, help_text='密码')
    ssl_enabled = serializers.BooleanField(default=False, help_text='SSL启用')
    connection_timeout = serializers.IntegerField(
        default=30,
        min_value=1,
        max_value=300,
        help_text='连接超时时间(秒)'
    )