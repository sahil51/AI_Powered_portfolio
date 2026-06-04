from rest_framework import serializers
from .models import ResearchTask

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResearchTask
        fields = '__all__'
        read_only_fields = [
            'owner'
        ]
        
    def validate_title(self, value):
        if len(value) < 5:
            raise serializers.ValidationError(
                'title must be at least 5 characters'
            )
        return value    