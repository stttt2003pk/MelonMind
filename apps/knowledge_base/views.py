from django.shortcuts import render
from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .models import KnowledgeEntry, KnowledgeQueryLog
from ..pdfloader.models import PDFDocument
from .serializers import KnowledgeEntrySerializer, KnowledgeQueryLogSerializer
from .connectors.mulves_client import MulvesClient


class KnowledgeEntryViewSet(viewsets.ModelViewSet):
    """Knowledge entry management viewset"""
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
    """Knowledge query viewset"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def search(self, request):
        """Search knowledge base"""
        query_text = request.data.get('query', '')
        if not query_text:
            return Response({'error': 'Query text is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Use Mulves client for searching
            mulves_client = MulvesClient()
            results = mulves_client.search(query_text)
            
            # Record query log
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
        """Get all categories"""
        categories = KnowledgeEntry.CATEGORY_CHOICES
        return Response([
            {'value': choice[0], 'label': choice[1]} 
            for choice in categories
        ])

@api_view(['GET'])
@permission_classes([AllowAny])  # Health check endpoints should be publicly accessible
def get_document_stats(request):
    """Get statistics about loaded documents"""
    total_docs = PDFDocument.objects.count()
    processed_docs = PDFDocument.objects.filter(status='completed').count()
    processing_docs = PDFDocument.objects.filter(status='processing').count()
    failed_docs = PDFDocument.objects.filter(status='failed').count()
    uploaded_docs = PDFDocument.objects.filter(status='uploaded').count()
    
    return Response({
        'total_documents': total_docs,
        'processed_documents': processed_docs,
        'processing_documents': processing_docs,
        'failed_documents': failed_docs,
        'uploaded_documents': uploaded_docs,
    })