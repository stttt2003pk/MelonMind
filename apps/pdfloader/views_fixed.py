
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

class PDFUploadView(APIView):
    """PDF文件上传和处理视图"""
    
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """
        上传PDF文件并开始处理流程
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
                page_count=0,
                milvus_connection_id=milvus_connection_id,
                collection_name=collection_name,
                status='uploaded'
            )
            
            # 使用Celery任务队列处理（推荐方式）
            from celery import current_app
            if current_app.control.inspect().stats():
                # 如果Celery可用，使用异步任务
                from .tasks import process_pdf_document_task
                process_pdf_document_task.delay(pdf_document.id, temp_file_path)
                message = 'PDF文件上传成功，已提交后台处理任务'
            else:
                # 如果Celery不可用，使用简单的线程处理
                import threading
                
                def process_document_in_thread():
                    try:
                        import asyncio
                        from asgiref.sync import sync_to_async
                        
                        async def async_process():
                            pipeline = PDFProcessingPipeline(milvus_connection_id)
                            try:
                                await sync_to_async(pdf_document.mark_as_processing)()
                                result = await pipeline.process_pdf_document(pdf_document, temp_file_path)
                                await sync_to_async(pdf_document.mark_as_completed)()
                                logger.info(f"PDF处理完成: {result}")
                            except Exception as e:
                                logger.error(f"PDF处理失败: {str(e)}")
                                await sync_to_async(pdf_document.mark_as_failed)(str(e))
                            finally:
                                # 清理临时文件
                                try:
                                    if os.path.exists(temp_file_path):
                                        os.remove(temp_file_path)
                                except Exception as cleanup_error:
                                    logger.warning(f"清理临时文件失败: {str(cleanup_error)}")
                        
                        # 在新线程中运行事件循环
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(async_process())
                        loop.close()
                        
                    except Exception as e:
                        logger.error(f"线程处理失败: {str(e)}")
                        pdf_document.mark_as_failed(str(e))
                        # 清理临时文件
                        try:
                            if os.path.exists(temp_file_path):
                                os.remove(temp_file_path)
                        except Exception as cleanup_error:
                            logger.warning(f"清理临时文件失败: {str(cleanup_error)}")
                
                thread = threading.Thread(target=process_document_in_thread)
                thread.daemon = True
                thread.start()
                message = 'PDF文件上传成功，正在后台处理'
            
            # 返回初始响应
            response_serializer = PDFDocumentSerializer(pdf_document)
            return Response({
                'success': True,
                'message': message,
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"PDF上传处理失败: {str(e)}")
            return Response({
                'success': False,
                'message': f"PDF处理失败: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
