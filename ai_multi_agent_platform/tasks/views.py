from rest_framework import viewsets
from .models import ResearchTask
from .serializers import TaskSerializer

class ResearchTaskView(viewsets.ModelViewSet):
    queryset = ResearchTask.objects.all()
    
    serializer_class = (TaskSerializer)