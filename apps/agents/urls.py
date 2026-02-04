from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AgentFlowViewSet, AgentExecutionViewSet

router = DefaultRouter()
router.register(r'flows', AgentFlowViewSet)
router.register(r'executions', AgentExecutionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]