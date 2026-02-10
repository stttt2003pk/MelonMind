from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import MulvesConnection, MulvesQueryLog, MulvesDataCache, VectorMetadata
from .serializers import (
    MulvesConnectionSerializer, MulvesConnectionDetailSerializer,
    MulvesQueryLogSerializer, MulvesDataCacheSerializer,
    MulvesQueryRequestSerializer, MulvesTestConnectionSerializer,
    VectorMetadataSerializer, VectorMetadataCreateSerializer, VectorMetadataUpdateSerializer
)
from .local_config import MilvusLocalConfig
from .connectors import MulvesDBService
# 使用Django REST Framework的标准异常


class MulvesConnectionViewSet(viewsets.ModelViewSet):
    """Mulves连接配置视图集"""
    queryset = MulvesConnection.objects.all()
    serializer_class = MulvesConnectionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MulvesConnectionDetailSerializer
        return super().get_serializer_class()
    
    @swagger_auto_schema(
        method='post',
        request_body=MulvesTestConnectionSerializer,
        responses={200: openapi.Response('连接测试结果')}
    )
    @action(detail=False, methods=['post'], url_path='test-connection')
    def test_connection(self, request):
        """测试数据库连接"""
        serializer = MulvesTestConnectionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                result = MulvesDBService.test_connection(serializer.validated_data)
                
                if result['success']:
                    return Response(result, status=status.HTTP_200_OK)
                else:
                    return Response(result, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response(
                    {'success': False, 'message': f'测试失败: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(['GET'])
@permission_classes([AllowAny])

def health_check(request):
    """Milvus连接健康检查API（无需认证）"""
    try:
        # 获取本地配置
        local_config = MilvusLocalConfig.get_local_config()
        
        # 同步测试连接
        result = MulvesDBService.test_connection(local_config)
        
        response_data = {
            'status': 'healthy' if result['success'] else 'unhealthy',
            'service': 'mulvesdb',
            'connection_host': local_config['host'],
            'connection_port': local_config['port'],
            'timestamp': timezone.now().isoformat(),
            'details': result['message']
        }
        
        status_code = status.HTTP_200_OK if result['success'] else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(response_data, status=status_code)
        
    except Exception as e:
        return Response(
            {
                'status': 'error',
                'service': 'mulvesdb',
                'timestamp': timezone.now().isoformat(),
                'error': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @swagger_auto_schema(
        method='get',
        responses={200: openapi.Response('连接状态列表')}
    )
    @action(detail=False, methods=['get'], url_path='connection-status')
    def connection_status(self, request):
        """获取所有连接的状态"""
        connections = self.get_queryset()
        status_list = []
        
        for conn in connections:
            status_info = {
                'id': conn.id,
                'name': conn.name,
                'host': conn.host,
                'is_active': conn.is_active,
                'last_query': None,
                'query_count': conn.query_logs.count()
            }
            
            last_log = conn.query_logs.order_by('-created_at').first()
            if last_log:
                status_info['last_query'] = last_log.created_at
            
            status_list.append(status_info)
        
        return Response(status_list)
    
    @action(detail=False, methods=['get'], url_path='test-local-connection')
    def test_local_connection(self, request):
        """测试本地Milvus连接（GET请求）"""
        try:
            # 获取本地配置
            local_config = MilvusLocalConfig.get_local_config()
            
            # 同步测试连接
            result = MulvesDBService.test_connection(local_config)
            
            response_data = {
                'success': result['success'],
                'message': result['message'],
                'connection_info': {
                    'host': local_config['host'],
                    'port': local_config['port'],
                    'database': local_config['database'],
                    'ssl_enabled': local_config['ssl_enabled'],
                    'connection_timeout': local_config['connection_timeout']
                },
                'timestamp': timezone.now().isoformat()
            }
            
            if result['success']:
                response_data['test_details'] = result.get('test_result', 'N/A')
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                response_data['error_details'] = result['message']
                return Response(response_data, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'message': f'测试执行失败: {str(e)}',
                    'timestamp': timezone.now().isoformat()
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MulvesQueryLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Mulves查询日志视图集"""
    queryset = MulvesQueryLog.objects.select_related('connection').all()
    serializer_class = MulvesQueryLogSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'connection_id', 
                openapi.IN_QUERY, 
                description="连接配置ID", 
                type=openapi.TYPE_INTEGER
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        """获取查询日志列表"""
        connection_id = request.query_params.get('connection_id')
        if connection_id:
            self.queryset = self.queryset.filter(connection_id=connection_id)
        return super().list(request, *args, **kwargs)


class MulvesDataCacheViewSet(viewsets.ModelViewSet):
    """Mulves数据缓存视图集"""
    queryset = MulvesDataCache.objects.all()
    serializer_class = MulvesDataCacheSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        method='delete',
        manual_parameters=[
            openapi.Parameter(
                'cache_key', 
                openapi.IN_QUERY, 
                description="缓存键", 
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={200: openapi.Response('清除缓存结果')}
    )
    @action(detail=False, methods=['delete'], url_path='clear-cache')
    def clear_cache(self, request):
        """清除缓存"""
        cache_key = request.query_params.get('cache_key')
        
        try:
            deleted_count = MulvesDBService.clear_cache(cache_key)
            
            return Response({
                'success': True,
                'message': f'成功清除 {deleted_count} 条缓存记录',
                'deleted_count': deleted_count
            })
        except Exception as e:
            return Response(
                {'success': False, 'message': f'清除缓存失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MulvesQueryViewSet(viewsets.ViewSet):
    """Mulves查询执行视图集"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=MulvesQueryRequestSerializer,
        responses={200: openapi.Response('查询结果')}
    )
    def create(self, request):
        """执行Mulves数据库查询"""
        serializer = MulvesQueryRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                result = MulvesDBService.execute_cached_query(
                    connection_id=serializer.validated_data['connection_id'],
                    sql=serializer.validated_data['query_sql'],
                    use_cache=serializer.validated_data['use_cache'],
                    cache_timeout=serializer.validated_data['cache_timeout']
                )
                
                if result['success']:
                    return Response(result, status=status.HTTP_200_OK)
                else:
                    return Response(result, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response(
                    {'success': False, 'message': f'查询执行失败: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VectorMetadataViewSet(viewsets.ModelViewSet):
    """向量元数据视图集"""
    queryset = VectorMetadata.objects.all()
    serializer_class = VectorMetadataSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return VectorMetadataCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return VectorMetadataUpdateSerializer
        return super().get_serializer_class()
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'collection_name', 
                openapi.IN_QUERY, 
                description="集合名称", 
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'source_document_id', 
                openapi.IN_QUERY, 
                description="源文档ID", 
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'status', 
                openapi.IN_QUERY, 
                description="状态", 
                type=openapi.TYPE_STRING
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        """获取向量元数据列表"""
        collection_name = request.query_params.get('collection_name')
        source_document_id = request.query_params.get('source_document_id')
        status_filter = request.query_params.get('status')
        
        queryset = self.get_queryset()
        
        if collection_name:
            queryset = queryset.filter(collection_name=collection_name)
        if source_document_id:
            queryset = queryset.filter(source_document_id=source_document_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        self.queryset = queryset.order_by('-created_at')
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        method='get',
        responses={200: openapi.Response('按文档统计信息')}
    )
    @action(detail=False, methods=['get'], url_path='stats-by-document')
    def stats_by_document(self, request):
        """按文档统计向量元数据"""
        collection_name = request.query_params.get('collection_name')
        
        queryset = self.get_queryset()
        if collection_name:
            queryset = queryset.filter(collection_name=collection_name)
            
        # 按文档ID分组统计
        from django.db.models import Count, Avg
        stats = queryset.values('source_document_id', 'collection_name').annotate(
            vector_count=Count('id'),
            avg_processing_time=Avg('processing_time_ms'),
            avg_importance=Avg('importance_level')
        ).order_by('-vector_count')
        
        return Response(stats)
    
    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'vector_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description='向量ID列表'
                ),
                'collection_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='集合名称'
                )
            },
            required=['vector_ids', 'collection_name']
        ),
        responses={200: openapi.Response('批量操作结果')}
    )
    @action(detail=False, methods=['post'], url_path='bulk-archive')
    def bulk_archive(self, request):
        """批量归档向量元数据"""
        vector_ids = request.data.get('vector_ids', [])
        collection_name = request.data.get('collection_name')
        
        if not vector_ids or not collection_name:
            return Response(
                {'success': False, 'message': '请提供向量ID列表和集合名称'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            affected_count = VectorMetadata.objects.filter(
                vector_id__in=vector_ids,
                collection_name=collection_name
            ).update(status='archived')
            
            return Response({
                'success': True,
                'message': f'成功归档 {affected_count} 条记录',
                'affected_count': affected_count
            })
        except Exception as e:
            return Response(
                {'success': False, 'message': f'批量归档失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'days_old': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='清理多少天前的数据'
                )
            }
        ),
        responses={200: openapi.Response('清理结果')}
    )
    @action(detail=False, methods=['post'], url_path='cleanup-old')
    def cleanup_old(self, request):
        """清理旧的向量元数据"""
        days_old = request.data.get('days_old', 90)
        
        try:
            deleted_count = VectorMetadata.cleanup_old_metadata(days_old)
            
            return Response({
                'success': True,
                'message': f'成功清理 {deleted_count} 条旧记录',
                'deleted_count': deleted_count,
                'days_old': days_old
            })
        except Exception as e:
            return Response(
                {'success': False, 'message': f'清理失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )