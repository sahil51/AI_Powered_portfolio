from rest_framework.routers import DefaultRouter
from .views import ResearchTaskViewSet

router = DefaultRouter()
router.register(r'tasks',ResearchTaskViewSet)
urlpatterns = router.urls