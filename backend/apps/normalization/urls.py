from rest_framework.routers import DefaultRouter
from .views import AgeGroupMappingViewSet

router = DefaultRouter()
router.register(r'age-groups', AgeGroupMappingViewSet, basename='age-group-mapping')

urlpatterns = router.urls
