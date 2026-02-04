from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import KnowledgeEntryViewSet, KnowledgeQueryViewSet

router = DefaultRouter()
router.register(r'entries', KnowledgeEntryViewSet)
router.register(r'query', KnowledgeQueryViewSet, basename='knowledge-query')

urlpatterns = [
    path('', include(router.urls)),
]