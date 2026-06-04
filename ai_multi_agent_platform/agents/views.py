from rest_framework import viewsets
from .models import Agent, AgentExecution
from .serializers import AgentSerializer, AgentExecutionSerializer
from accounts.permissions import IsAdminRole
from rest_framework.generics import ListAPIView, RetrieveAPIView

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .crew import AgentCrew
from .serializers import CrewSerializer

from django.db.models import Count
class CrewAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request):

        serializer = CrewSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        result = AgentCrew.execute(
            request.user,
            serializer.validated_data[
                "query"
            ]
        )

        return Response(result)

class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer
    permission_classes = [IsAdminRole]
    
    
    def get_queryset(self):
        return Agent.objects.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class AgentExecutionListView(ListAPIView):

    queryset = AgentExecution.objects.all().order_by(
        "-created_at"
    )

    serializer_class = AgentExecutionSerializer




class AgentExecutionDetailView(
    RetrieveAPIView
):

    queryset = AgentExecution.objects.all()

    serializer_class = (
        AgentExecutionSerializer
    )

class AnalyticsAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        data = (
            AgentExecution.objects
            .values("agent_type")
            .annotate(
                count=Count("id")
            )
        )

        return Response({
            "total_executions":
            AgentExecution.objects.count(),

            "agents": data
        })