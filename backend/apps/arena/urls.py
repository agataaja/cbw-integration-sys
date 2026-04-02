from django.urls import path

from . import views

app_name = 'apps.arena'

urlpatterns = [
    path('', views.index, name='base'),
    path('preview/', views.preview_view, name='preview'),
    path('arena-web-hooking/', views.arena_receiver, name='arena-web-hooking'),
    path('arena-web-hooking-show/', views.arena_show, name='arena-web-hooking-show'),
    path('pbi-repo/', views.pbi_view, name='pbi-repo'),
    path('lutas-json/', views.lutas_json),
    path("credentials/", views.credentials_list, name="credentials_list"),
    path("credentials/new/", views.credentials_create, name="credentials_create"),
    path("credentials/<int:pk>/edit/", views.credentials_edit, name="credentials_edit"),
    path("credentials/<int:pk>/delete/", views.credentials_delete, name="credentials_delete"),
    path('eventos-sge/', views.eventos_sge_list, name='eventos_sge_list'),
    path('sync_eventos_sge/', views.sync_eventos_sge, name='sync_eventos_sge'),
    path("credentials/<int:pk>/sync/", views.sync_eventos_arena, name="sync_eventos_arena"),
    path("eventos-arena/<int:pk>", views.eventos_arena_list, name="eventos_arena_list"),
    path("arena/<int:pk_arena>/associate-sge/<int:pk_sge>/", views.associate_sge_arena_event,
         name="associate_sge_arena_event"),
    path("sge/<int:pk_sge>/associate-arena/", views.select_arena_for_sge, name="associate_arena_event"),


]
