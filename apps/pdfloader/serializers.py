from rest_framework import serializers
from .models import PDFDocument, PDFChunk


class PDFDocumentSerializer(serializers.ModelSerializer):
    """PDF文档序列化器"""
    
    class Meta:
        model = PDFDocument
        fields = [
            'id', 'title', 'file_path', 'file_size', 'file_hash', 'page_count',
            'status', 'milvus_connection', 'collection_name',
            'error_message', 'created_at', 'updated_at', 'processed_at'
        ]
        read_only_fields = ['id', 'status', 'error_message', 'created_at', 'updated_at', 'processed_at']
        extra_kwargs = {
            'file_hash': {'read_only': True},  # 哈希值由系统自动生成
        }


class PDFDocumentCreateSerializer(serializers.ModelSerializer):
    """PDF文档创建序列化器"""
    
    class Meta:
        model = PDFDocument
        fields = [
            'title', 'file_path', 'milvus_connection', 'collection_name'
        ]
    
    def validate_file_path(self, value):
        """验证文件路径"""
        import os
        if not os.path.exists(value):
            raise serializers.ValidationError("文件路径不存在")
        if not value.lower().endswith('.pdf'):
            raise serializers.ValidationError("文件必须是PDF格式")
        return value
    
    def validate_collection_name(self, value):
        """验证集合名称"""
        if not value:
            raise serializers.ValidationError("集合名称不能为空")
        # 检查集合名称格式
        import re
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', value):
            raise serializers.ValidationError("集合名称只能包含字母、数字和下划线，且必须以字母开头")
        return value


class PDFChunkSerializer(serializers.ModelSerializer):
    """PDF分块序列化器"""
    
    class Meta:
        model = PDFChunk
        fields = [
            'id', 'document', 'chunk_index', 'content', 'page_number',
            'vector_id', 'embedding_model', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'vector_id', 'created_at']


class PDFUploadSerializer(serializers.Serializer):
    """PDF文件上传序列化器"""
    
    title = serializers.CharField(max_length=500, required=True)
    file = serializers.FileField(required=True)
    milvus_connection_id = serializers.IntegerField(required=True)
    collection_name = serializers.CharField(max_length=100, required=True)
    
    def validate_file(self, value):
        """验证上传的文件"""
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("只支持PDF文件上传")
        
        # 检查文件大小（限制为50MB）
        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError("文件大小不能超过50MB")
            
        return value
    
    def validate_collection_name(self, value):
        """验证集合名称"""
        import re
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', value):
            raise serializers.ValidationError("集合名称只能包含字母、数字和下划线，且必须以字母开头")
        return value


class VectorSearchSerializer(serializers.Serializer):
    """向量搜索序列化器"""
    
    query_text = serializers.CharField(required=True, max_length=1000)
    collection_name = serializers.CharField(required=True)
    limit = serializers.IntegerField(default=10, min_value=1, max_value=100)


class ProcessingStatusSerializer(serializers.ModelSerializer):
    """处理状态序列化器"""
    
    chunks_count = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = PDFDocument
        fields = [
            'id', 'title', 'status', 'error_message', 
            'created_at', 'processed_at', 'chunks_count', 'success_rate'
        ]
    
    def get_chunks_count(self, obj):
        """获取分块数量"""
        return obj.chunks.count()
    
    def get_success_rate(self, obj):
        """计算成功率"""
        total_chunks = obj.chunks.count()
        if total_chunks == 0:
            return 0
        # 假设有vector_id的chunk是成功的
        successful_chunks = obj.chunks.exclude(vector_id__isnull=True).count()
        return round((successful_chunks / total_chunks) * 100, 2)