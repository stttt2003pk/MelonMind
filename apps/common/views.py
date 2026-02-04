from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def home_page(request):
    """
    用户友好的HTML主页 - 正常HTTP访问
    """
    logger.info("HTML homepage accessed")
    context = {
        'title': 'MelonMind - 智能运维助手',
        'version': '1.0.0',
        'features': [
            {
                'name': '智能代理',
                'description': '基于LangChain和LangGraph的强大AI代理系统'
            },
            {
                'name': '知识库',
                'description': '集成Mulves连接器的网络运维知识库'
            },
            {
                'name': '实时监控',
                'description': '实时监控系统状态和性能指标'
            }
        ]
    }
    return render(request, 'home.html', context)

@api_view(['GET'])
def api_home(request):
    """
    API首页 - 返回JSON格式的系统信息
    """
    logger.info("API home page accessed")
    return Response({
        "message": "Welcome to MelonMind API",
        "status": "success",
        "version": "1.0.0",
        "endpoints": {
            "agents": "/api/agents/",
            "knowledge_base": "/api/knowledge/",
            "admin": "/admin/"
        }
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint - allows anonymous access
    Bypasses DRF permission validation for monitoring and health checks
    """
    return Response({
        "status": "healthy",
        "service": "MelonMind API"
    }, status=status.HTTP_200_OK)