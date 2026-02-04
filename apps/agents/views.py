from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import AgentFlow, AgentExecution
from .serializers import AgentFlowSerializer, AgentExecutionSerializer
from .flows.network_ops import NetworkOperationsFlow


class AgentFlowViewSet(viewsets.ModelViewSet):
    """Agent flow management viewset"""
    queryset = AgentFlow.objects.all()
    serializer_class = AgentFlowSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute specified Agent flow"""
        flow = self.get_object()
        input_data = request.data.get('input_data', {})
        
        # Create execution record
        execution = AgentExecution.objects.create(
            flow=flow,
            input_data=input_data,
            status='pending'
        )
        
        try:
            # Select corresponding executor based on flow type
            if 'network' in flow.name.lower():
                flow_executor = NetworkOperationsFlow()
            else:
                # Default executor
                flow_executor = NetworkOperationsFlow()
            
            # Execute flow asynchronously
            from celery import current_app
            current_app.send_task(
                'apps.agents.tasks.execute_agent_flow',
                args=[execution.id, input_data]
            )
            
            return Response({
                'message': 'Flow execution started',
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
    """Agent execution record viewset"""
    queryset = AgentExecution.objects.all()
    serializer_class = AgentExecutionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AgentExecution.objects.filter(flow__created_by=self.request.user)