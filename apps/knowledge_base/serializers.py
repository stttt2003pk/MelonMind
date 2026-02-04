from rest_framework import serializers
from .models import KnowledgeEntry, KnowledgeQueryLog


class KnowledgeEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeEntry
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at')


class KnowledgeQueryLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = KnowledgeQueryLog
        fields = '__all__'
        read_only_fields = ('user', 'created_at')