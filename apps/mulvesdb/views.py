from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import asyncio

from .models import MulvesConnection, MulvesQueryLog, MulvesDataCache
from .serializers import (
    MulvesConnectionSerializer, MulvesConnectionDetailSerializer,
    MulvesQueryLogSerializer, MulvesDataCacheSerializer,
    MulvesQueryRequestSerializer, MulvesTestConnectionSerializer
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
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    MulvesDBService.test_connection(serializer.validated_data)
                )
                loop.close()
                
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
        
        # 异步测试连接
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            MulvesDBService.test_connection(local_config)
        )
        loop.close()
        
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
            
            # 异步测试连接
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                MulvesDBService.test_connection(local_config)
            )
            loop.close()
            
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
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            deleted_count = loop.run_until_complete(
                MulvesDBService.clear_cache(cache_key)
            )
            loop.close()
            
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
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    MulvesDBService.execute_cached_query(
                        connection_id=serializer.validated_data['connection_id'],
                        sql=serializer.validated_data['query_sql'],
                        use_cache=serializer.validated_data['use_cache'],
                        cache_timeout=serializer.validated_data['cache_timeout']
                    )
                )
                loop.close()
                
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