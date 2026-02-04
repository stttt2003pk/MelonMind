from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import KnowledgeEntry, KnowledgeQueryLog
from .serializers import KnowledgeEntrySerializer, KnowledgeQueryLogSerializer
from .connectors.mulves_client import MulvesClient


class KnowledgeEntryViewSet(viewsets.ModelViewSet):
    """知识条目管理视图集"""
    queryset = KnowledgeEntry.objects.filter(is_published=True)
    serializer_class = KnowledgeEntrySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        search = self.request.query_params.get('search')
        
        if category:
            queryset = queryset.filter(category=category)
        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search) |
                models.Q(content__icontains=search) |
                models.Q(tags__icontains=search)
            )
        return queryset


class KnowledgeQueryViewSet(viewsets.ViewSet):
    """知识查询视图集"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def search(self, request):
        """搜索知识库"""
        query_text = request.data.get('query', '')
        if not query_text:
            return Response({'error': 'Query text is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 使用 Mulves 客户端进行搜索
            mulves_client = MulvesClient()
            results = mulves_client.search(query_text)
            
            # 记录查询日志
            KnowledgeQueryLog.objects.create(
                query_text=query_text,
                results_count=len(results),
                user=request.user
            )
            
            return Response({
                'query': query_text,
                'results': results,
                'count': len(results)
            })
            
        except Exception as e:
            return Response({'error': str(e)}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """获取所有分类"""
        categories = KnowledgeEntry.CATEGORY_CHOICES
        return Response([
            {'value': choice[0], 'label': choice[1]} 
            for choice in categories
        ])