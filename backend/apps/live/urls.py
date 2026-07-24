from django.urls import path

from .views import (
    ArenaClientDetailAPIView,
    ArenaClientListCreateAPIView,
    ArenaFightListAPIView,
    ArenaFighterListAPIView,
    ArenaSportEventListAPIView,
    ArenaWebhookAPIView,
    TunnelRegisterAPIView,
)
app_name = 'apps.live'

urlpatterns = [
    path('clients/', ArenaClientListCreateAPIView.as_view(), name='arena-clients-list-create'),
    path('clients/<int:pk>/', ArenaClientDetailAPIView.as_view(), name='arena-clients-detail'),
    path('arena-webhook/', ArenaWebhookAPIView.as_view(), name='arena-api-webhook'),
    path('sport-events/', ArenaSportEventListAPIView.as_view(), name='arena-sport-events-list'),
    path('fights/', ArenaFightListAPIView.as_view(), name='arena-fights-list'),
    path('fighters/', ArenaFighterListAPIView.as_view(), name='arena-fighters-list'),
    path('tunnel/register/', TunnelRegisterAPIView.as_view(), name='arena-tunnel-register'),
]
