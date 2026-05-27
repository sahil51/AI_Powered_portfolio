from rest_framework.routers import DefaultRouter
from .views import ResearchTaskView

router = DefaultRouter()
router.register(r'tasks',ResearchTaskView)
urlpatterns = router.urls