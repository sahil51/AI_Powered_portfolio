from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AgentViewSet,
    AgentExecutionListView,
    AgentExecutionDetailView,
    CrewAPIView,
    AnalyticsAPIView
)

router = DefaultRouter()
router.register(r'agents', AgentViewSet)

urlpatterns = router.urls + [

    path(
        "executions/",
        AgentExecutionListView.as_view(),
        name="agent-executions"
    ),

    path(
        "executions/<int:pk>/",
        AgentExecutionDetailView.as_view(),
        name="execution-detail"
    ),
 
    path(
    "crew/",
    CrewAPIView.as_view(),
    name="crew-api"
),

    path(
    "analytics/",
    AnalyticsAPIView.as_view(),
    name="analytics"
)   

]