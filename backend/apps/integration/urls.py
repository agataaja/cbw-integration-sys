from rest_framework.routers import DefaultRouter
from .views import (
    ArenaClientsBridgeViewSet,
    ArenaEventRankingSyncView,
    ArenaEventSnapshotView,
    EventosArenaViewSet,
    EventosBridgeViewSet,
    EventosSgeViewSet,
    NormalizedRankingView,
)
from django.urls import path

router = DefaultRouter()
router.register(r'eventos-arena', EventosArenaViewSet)
router.register(r'eventos-sge', EventosSgeViewSet)
router.register(r'bridge/eventos', EventosBridgeViewSet, basename='eventos-match')
router.register(r'bridge/clients', ArenaClientsBridgeViewSet, basename='clients-match')

urlpatterns = router.urls

urlpatterns += [
    path('normalized-ranking/<int:event_id>/', NormalizedRankingView.as_view(), name='normalized-ranking'),
    path('arena-events/<str:arena_event_id>/snapshot/', ArenaEventSnapshotView.as_view(), name='arena-event-snapshot'),
    path('arena-events/<str:arena_event_id>/sync-rankings/', ArenaEventRankingSyncView.as_view(), name='arena-event-sync-rankings'),
]

