from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import AgentFlow, AgentExecution
from .serializers import AgentFlowSerializer, AgentExecutionSerializer
from .flows.network_ops import NetworkOperationsFlow


class AgentFlowViewSet(viewsets.ModelViewSet):
    """Agent 流程管理视图集"""
    queryset = AgentFlow.objects.all()
    serializer_class = AgentFlowSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """执行指定的 Agent 流程"""
        flow = self.get_object()
        input_data = request.data.get('input_data', {})
        
        # 创建执行记录
        execution = AgentExecution.objects.create(
            flow=flow,
            input_data=input_data,
            status='pending'
        )
        
        try:
            # 根据流程类型选择对应的执行器
            if 'network' in flow.name.lower():
                flow_executor = NetworkOperationsFlow()
            else:
                # 默认执行器
                flow_executor = NetworkOperationsFlow()
            
            # 异步执行流程
            from celery import current_app
            current_app.send_task(
                'apps.agents.tasks.execute_agent_flow',
                args=[execution.id, input_data]
            )
            
            return Response({
                'message': '流程已启动执行',
                'execution_id': execution.id
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            execution.status = 'failed'
            execution.error_message = str(e)
            execution.save()
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AgentExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """Agent 执行记录视图集"""
    queryset = AgentExecution.objects.all()
    serializer_class = AgentExecutionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AgentExecution.objects.filter(flow__created_by=self.request.user)