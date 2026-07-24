from django.urls import path

from .views import (
    ArenaClientDetailAPIView,
    ArenaClientListCreateAPIView,
    ArenaEventStructureSyncAPIView,
    ArenaFightListAPIView,
    ArenaFighterListAPIView,
    ArenaSportEventListAPIView,
    ArenaSportEventSyncAPIView,
    
    
)
app_name = 'apps.arena'

urlpatterns = [
    path('clients/', ArenaClientListCreateAPIView.as_view(), name='arena-clients-list-create'),
    path('clients/<int:pk>/', ArenaClientDetailAPIView.as_view(), name='arena-clients-detail'),
    path('sync/sport-events/', ArenaSportEventSyncAPIView.as_view(), name='arena-sync-sport-events'),
    path('sync/event-structure/', ArenaEventStructureSyncAPIView.as_view(), name='arena-sync-event-structure'),
    path('sport-events/', ArenaSportEventListAPIView.as_view(), name='arena-sport-events-list'),
    path('fights/', ArenaFightListAPIView.as_view(), name='arena-fights-list'),
    path('fighters/', ArenaFighterListAPIView.as_view(), name='arena-fighters-list'),
]
