import os
import tempfile
import logging
from django.http import JsonResponse
from rest_framework import status, generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

from apps.common.exceptions import MelonMindException
from .models import PDFDocument, PDFChunk
from .serializers import (
    PDFDocumentSerializer, PDFDocumentCreateSerializer, 
    PDFChunkSerializer, PDFUploadSerializer, 
    VectorSearchSerializer, ProcessingStatusSerializer
)
from .storage import PDFProcessingPipeline

logger = logging.getLogger(__name__)


class PDFDocumentListView(generics.ListCreateAPIView):
    """PDF文档列表和创建视图"""
    
    queryset = PDFDocument.objects.all()
    serializer_class = PDFDocumentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'milvus_connection']
    search_fields = ['title', 'file_path']
    ordering_fields = ['created_at', 'updated_at', 'processed_at']
    ordering = ['-created_at']


class PDFDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """PDF文档详情视图"""
    
    queryset = PDFDocument.objects.all()
    serializer_class = PDFDocumentSerializer


class PDFDocumentChunksView(generics.ListAPIView):
    """PDF文档分块列表视图"""
    
    serializer_class = PDFChunkSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['page_number']
    ordering_fields = ['chunk_index', 'page_number']
    ordering = ['chunk_index']
    
    def get_queryset(self):
        document_id = self.kwargs['pk']
        return PDFChunk.objects.filter(document_id=document_id)


class PDFUploadView(APIView):
    """PDF文件上传和处理视图"""
    
    parser_classes = [MultiPartParser, FormParser]
    
    async def post(self, request):
        """
        上传PDF文件并开始处理流程
        
        请求参数:
        - title: 文档标题
        - file: PDF文件
        - milvus_connection_id: Milvus连接ID
        - collection_name: 集合名称
        """
        serializer = PDFUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': "请求数据验证失败",
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 保存上传的文件
            uploaded_file = request.FILES['file']
            title = serializer.validated_data['title']
            milvus_connection_id = serializer.validated_data['milvus_connection_id']
            collection_name = serializer.validated_data['collection_name']
            
            # 生成临时文件路径
            temp_filename = f"temp_{uploaded_file.name}"
            temp_file_path = os.path.join(tempfile.gettempdir(), temp_filename)
            
            # 保存文件到临时位置
            with open(temp_file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            # 创建PDF文档记录
            pdf_document = PDFDocument.objects.create(
                title=title,
                file_path=temp_file_path,
                file_size=uploaded_file.size,
                page_count=0,  # 后续处理时更新
                milvus_connection_id=milvus_connection_id,
                collection_name=collection_name,
                status='uploaded'
            )
            
            # 异步启动处理流程
            import asyncio
            from asgiref.sync import sync_to_async
            
            async def process_document():
                pipeline = PDFProcessingPipeline(milvus_connection_id)
                try:
                    result = await pipeline.process_pdf_document(pdf_document, temp_file_path)
                    logger.info(f"PDF处理完成: {result}")
                except Exception as e:
                    logger.error(f"PDF处理失败: {str(e)}")
                    # 更新文档状态为失败
                    await sync_to_async(pdf_document.mark_as_failed)(str(e))
                finally:
                    # 清理临时文件
                    try:
                        if os.path.exists(temp_file_path):
                            os.remove(temp_file_path)
                    except Exception as cleanup_error:
                        logger.warning(f"清理临时文件失败: {str(cleanup_error)}")
            
            # 在后台运行处理任务
            asyncio.create_task(process_document())
            
            # 返回初始响应
            response_serializer = PDFDocumentSerializer(pdf_document)
            return Response({
                'success': True,
                'message': 'PDF文件上传成功，正在后台处理',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"PDF上传处理失败: {str(e)}")
            return Response({
                'success': False,
                'message': f"PDF处理失败: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PDFProcessingStatusView(APIView):
    """PDF处理状态查询视图"""
    
    def get(self, request, pk):
        """获取PDF文档处理状态"""
        try:
            document = PDFDocument.objects.get(pk=pk)
            serializer = ProcessingStatusSerializer(document)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except PDFDocument.DoesNotExist:
            return Response({
                'success': False,
                'message': "文档不存在"
            }, status=status.HTTP_404_NOT_FOUND)


class VectorSearchView(APIView):
    """向量搜索视图"""
    
    async def post(self, request):
        """
        执行向量相似度搜索
        
        请求参数:
        - query_text: 查询文本
        - collection_name: 集合名称
        - limit: 返回结果数量限制
        """
        serializer = VectorSearchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': "请求数据验证失败",
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            query_text = serializer.validated_data['query_text']
            collection_name = serializer.validated_data['collection_name']
            limit = serializer.validated_data['limit']
            
            # 这里需要确定使用哪个Milvus连接
            # 简单起见，使用第一个活跃的连接
            from apps.mulvesdb.models import MulvesConnection
            active_connection = await MulvesConnection.objects.filter(is_active=True).afirst()
            
            if not active_connection:
                return Response({
                    'success': False,
                    'message': "没有可用的Milvus连接"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 执行向量搜索
            from .storage import PDFVectorStorageService
            async with PDFVectorStorageService(active_connection.id) as storage_service:
                results = await storage_service.search_similar_chunks(
                    collection_name=collection_name,
                    query_text=query_text,
                    limit=limit
                )
            
            return Response({
                'success': True,
                'message': '搜索完成',
                'data': results,
                'query_info': {
                    'query_text': query_text,
                    'collection_name': collection_name,
                    'limit': limit
                }
            })
            
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            return Response({
                'success': False,
                'message': f"搜索失败: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PDFCollectionInfoView(APIView):
    """PDF集合信息视图"""
    
    async def get(self, request, collection_name):
        """获取集合信息"""
        try:
            # 使用活跃的Milvus连接
            from apps.mulvesdb.models import MulvesConnection
            active_connection = await MulvesConnection.objects.filter(is_active=True).afirst()
            
            if not active_connection:
                return Response({
                    'success': False,
                    'message': "没有可用的Milvus连接"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            from .storage import PDFVectorStorageService
            async with PDFVectorStorageService(active_connection.id) as storage_service:
                collection_info = await storage_service.get_collection_info(collection_name)
            
            return Response({
                'success': True,
                'data': collection_info
            })
            
        except Exception as e:
            logger.error(f"获取集合信息失败: {str(e)}")
            return Response({
                'success': False,
                'message': f"获取集合信息失败: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)