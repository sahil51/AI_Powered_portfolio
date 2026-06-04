from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import ResearchTask
from .serializers import TaskSerializer
from .services import create_task
from rest_framework.permissions import IsAuthenticated
from .tasks import process_research_task

class ResearchTaskViewSet(viewsets.ModelViewSet):
    queryset = ResearchTask.objects.all()
    serializer_class = (TaskSerializer)
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ResearchTask.objects.filter(owner=self.request.user)

    def create(self, request):

        serializer = (self.get_serializer(data=request.data))

        serializer.is_valid(raise_exception=True)

        task = create_task(request.user,serializer.validated_data)

        response_serializer = (TaskSerializer(task))
        process_research_task.delay(task.id)
        return Response(response_serializer.data,status=status.HTTP_201_CREATED)