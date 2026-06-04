from rest_framework import serializers
from .models import Agent, AgentExecution

class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = "__all__"
        read_only_fields = ['owner']
        
    def validate_name(self,value):
        if len(value)<3:
            raise serializers.ValidationError(
                'Name too short'
            )
            
        return value





class AgentExecutionSerializer(serializers.ModelSerializer):

    class Meta:
        model = AgentExecution
        fields = "__all__"


class CrewSerializer(serializers.Serializer):

    query = serializers.CharField()