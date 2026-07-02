"""
URL configuration for SGE app.
Routes for ranking and fight data CRUD operations.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ResultadoSGEViewSet, LutaSGEViewSet

app_name = 'sge'

# Create router and register ViewSets
router = DefaultRouter()
router.register(r'rankings', ResultadoSGEViewSet, basename='resultado-sge')
router.register(r'fights', LutaSGEViewSet, basename='luta-sge')

urlpatterns = [
    path('', include(router.urls)),
]

# Available endpoints:
# GET    /api/sge/rankings/                          - List all rankings
# POST   /api/sge/rankings/                          - Create ranking
# GET    /api/sge/rankings/{id}/                     - Retrieve specific ranking
# PUT    /api/sge/rankings/{id}/                     - Update specific ranking
# DELETE /api/sge/rankings/{id}/                     - Delete specific ranking
# GET    /api/sge/rankings/by-event/{event_id}/      - Get all rankings by event_id
# DELETE /api/sge/rankings/bulk-delete-by-event/     - Bulk delete rankings by event_id
# PUT    /api/sge/rankings/bulk-update-by-event/     - Bulk update rankings by event_id
#
# GET    /api/sge/fights/                            - List all fights
# POST   /api/sge/fights/                            - Create fight
# GET    /api/sge/fights/{id}/                       - Retrieve specific fight
# PUT    /api/sge/fights/{id}/                       - Update specific fight
# DELETE /api/sge/fights/{id}/                       - Delete specific fight
# GET    /api/sge/fights/by-event/{event_id}/        - Get all fights by event_id
# DELETE /api/sge/fights/bulk-delete-by-event/       - Bulk delete fights by event_id
# PUT    /api/sge/fights/bulk-update-by-event/       - Bulk update fights by event_id
