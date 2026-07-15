from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .models import ArenaClient, ArenaFight, ArenaFighter, ArenaSportEvent, Tunnel
from .serializers import (
    ArenaClientSerializer,
    ArenaClientSyncRequestSerializer,
    ArenaEventSyncRequestSerializer,
    ArenaFightSerializer,
    ArenaFighterSerializer,
    ArenaSportEventSerializer,
    ArenaWebhookRequestSerializer,
    TunnelRegisterSerializer,
)
from .services.sync import sync_event_structure, sync_sport_events
from .services.webhook_ingress import ingest_arena_webhook


class ArenaSportEventPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class ArenaClientListCreateAPIView(APIView):
    def get(self, request):
        queryset = ArenaClient.objects.all().order_by("id")
        serializer = ArenaClientSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ArenaClientSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ArenaClientDetailAPIView(APIView):
    def get(self, request, pk):
        instance = get_object_or_404(ArenaClient, pk=pk)
        serializer = ArenaClientSerializer(instance)
        return Response(serializer.data)

    def put(self, request, pk):
        instance = get_object_or_404(ArenaClient, pk=pk)
        serializer = ArenaClientSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, pk):
        instance = get_object_or_404(ArenaClient, pk=pk)
        serializer = ArenaClientSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        instance = get_object_or_404(ArenaClient, pk=pk)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ArenaWebhookAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = ArenaWebhookRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = ingest_arena_webhook(serializer.validated_data)
        return Response(result)


class ArenaSportEventSyncAPIView(APIView):
    def post(self, request):
        serializer = ArenaClientSyncRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = sync_sport_events(serializer.validated_data["arena_client_id"])
        return Response(result, status=status.HTTP_200_OK)


class ArenaEventStructureSyncAPIView(APIView):
    def post(self, request):
        serializer = ArenaEventSyncRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = sync_event_structure(
            serializer.validated_data["arena_client_id"],
            serializer.validated_data["arena_event_id"],
        )
        return Response(result, status=status.HTTP_200_OK)


class ArenaSportEventListAPIView(APIView):
    def get(self, request):
        arena_client_id = request.query_params.get("arena_client_id")
        queryset = ArenaSportEvent.objects.all().order_by("id")
        if arena_client_id:
            queryset = queryset.filter(arena_client_id=arena_client_id)
        paginator = ArenaSportEventPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = ArenaSportEventSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ArenaFightListAPIView(APIView):
    def get(self, request):
        arena_event_id = request.query_params.get("arena_event_id")
        queryset = ArenaFight.objects.select_related("arena_sport_event_weight_category").order_by("id")
        if arena_event_id:
            queryset = queryset.filter(arena_sport_event_weight_category__arena_sport_event__event_id=str(arena_event_id))
        serializer = ArenaFightSerializer(queryset, many=True)
        return Response(serializer.data)


class ArenaFighterListAPIView(APIView):
    def get(self, request):
        fight_id = request.query_params.get("fight_id")
        queryset = ArenaFighter.objects.select_related("fight").order_by("id")
        if fight_id:
            queryset = queryset.filter(fight__fight_id=str(fight_id))
        serializer = ArenaFighterSerializer(queryset, many=True)
        return Response(serializer.data)
    

class TunnelRegisterAPIView(APIView):

    authentication_classes = []
    permission_classes = []

    def post(self, request):

        serializer = TunnelRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        tunnel = Tunnel.objects.get(instance=data["instance"])

        tunnel.status = data["status"]
        tunnel.public_url = (data.get("public_url", None))
        tunnel.last_seen = timezone.now()
        tunnel.save(
            update_fields=[
                "status",
                "public_url",
                "last_seen"
            ]
        )

        return Response({
            "message": "Tunnel updated"
        })
