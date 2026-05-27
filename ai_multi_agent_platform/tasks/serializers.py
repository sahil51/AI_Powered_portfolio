from rest_framework import serializers
from .models import ResearchTask

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResearchTask
        fields = '__all__'
        
    def validate_name(self,value):
        if len(value)<5:
            raise serializers.ValidationError(
                'title must be  at least 5 characters'
            )
        return value