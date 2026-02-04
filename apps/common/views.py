from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

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