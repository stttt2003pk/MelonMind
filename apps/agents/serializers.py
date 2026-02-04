from rest_framework import serializers
from .models import AgentFlow, AgentExecution


class AgentFlowSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentFlow
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at')


class AgentExecutionSerializer(serializers.ModelSerializer):
    flow_name = serializers.CharField(source='flow.name', read_only=True)
    
    class Meta:
        model = AgentExecution
        fields = '__all__'
        read_only_fields = ('started_at', 'completed_at', 'created_at')