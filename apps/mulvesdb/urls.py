from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建路由器
router = DefaultRouter()
router.register(r'connections', views.MulvesConnectionViewSet, basename='mulves-connection')
router.register(r'query-logs', views.MulvesQueryLogViewSet, basename='mulves-query-log')
router.register(r'data-cache', views.MulvesDataCacheViewSet, basename='mulves-data-cache')
router.register(r'queries', views.MulvesQueryViewSet, basename='mulves-query')

urlpatterns = [
    path('', include(router.urls)),
    path('health/', views.health_check, name='mulves-health-check'),
]