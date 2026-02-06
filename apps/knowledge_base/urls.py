from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import KnowledgeEntryViewSet, KnowledgeQueryViewSet, get_document_stats

router = DefaultRouter()
router.register(r'entries', KnowledgeEntryViewSet)
router.register(r'query', KnowledgeQueryViewSet, basename='knowledge-query')

urlpatterns = [
    path('', include(router.urls)),
    path('document-stats/', get_document_stats, name='document-stats'),
]