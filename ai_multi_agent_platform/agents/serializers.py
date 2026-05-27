from rest_framework import serializers
from .models import Agent

class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = "__all__"
        
    def validate_name(self,value):
        if len(value)<3:
            raise serializers.ValidationError(
                'Name too short'
            )
            
        return value