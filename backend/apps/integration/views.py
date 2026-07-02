from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.integration.models import ClientBridge, EventBridge
from apps.sge.models import GestaoEventos, LutaSGE
from apps.normalization.models import IdClassePeso
from .serializers import (
	ArenaClientsBridgeSerializer,
	ArenaClientsBridgeWriteSerializer,
	ArenaEventSnapshotRequestSerializer,
	ArenaEventSyncRequestSerializer,
	BridgeCredentialRequestSerializer,
	EventosArenaSerializer,
	EventosBridgeSerializer,
	EventosSgeSerializer,
)
from .services import (
	build_event_snapshot,
	build_bridge_snapshot,
	sync_event_rankings_to_sge,
	sync_bridge_rankings_to_sge,
	sync_bridge_fights_to_sge,
)
from .services.arena_sge import ArenaIntegrationError


class EventosArenaViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = EventBridge.objects.select_related('arena_event', 'sge_event').all()
	serializer_class = EventosArenaSerializer


class EventosBridgeViewSet(viewsets.ModelViewSet):
	queryset = EventBridge.objects.select_related('arena_event', 'sge_event').all().order_by('-id')

	def get_serializer_class(self):
		if self.action in ('list', 'retrieve'):
			return EventosArenaSerializer
		elif self.action in ('snapshot', 'sync_rankings', 'sync_fights'):
			return BridgeCredentialRequestSerializer
		return EventosBridgeSerializer
	
	@action(detail=True, methods=['get'], url_path='snapshot')
	def snapshot(self, request, pk=None):
		"""Get Arena event snapshot (rankings + fights) for this EventBridge."""
		serializer = self.get_serializer(data=request.query_params)
		serializer.is_valid(raise_exception=True)
		
		try:
			snapshot = build_bridge_snapshot(
				credentials_pk=serializer.validated_data["credential_id"],
				event_bridge_id=int(pk),
			)
		except ArenaIntegrationError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
		
		return Response(snapshot)
	
	@action(detail=True, methods=['post'], url_path='sync-rankings')
	def sync_rankings(self, request, pk=None):
		"""Sync rankings from Arena to SGE for this EventBridge."""
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		
		try:
			result = sync_bridge_rankings_to_sge(
				credentials_pk=serializer.validated_data["credential_id"],
				event_bridge_id=int(pk),
			)
		except ArenaIntegrationError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
		
		return Response(result, status=status.HTTP_200_OK)
	
	@action(detail=True, methods=['post'], url_path='sync-fights')
	def sync_fights(self, request, pk=None):
		"""Sync fights from Arena to SGE for this EventBridge."""
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		
		try:
			result = sync_bridge_fights_to_sge(
				credentials_pk=serializer.validated_data["credential_id"],
				event_bridge_id=int(pk),
			)
		except ArenaIntegrationError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
		
		return Response(result, status=status.HTTP_200_OK)


class ArenaClientsBridgeViewSet(viewsets.ModelViewSet):
	queryset = ClientBridge.objects.select_related('arena_client').prefetch_related('eventos_match').all().order_by('-id')

	def get_serializer_class(self):
		if self.action in ('list', 'retrieve'):
			return ArenaClientsBridgeSerializer
		return ArenaClientsBridgeWriteSerializer


class EventosSgeViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = GestaoEventos.objects.all()
	serializer_class = EventosSgeSerializer


class NormalizedRankingView(APIView):
	def get(self, request, event_id):
		lutas = LutaSGE.objects.filter(id_evento=event_id)
		normalized = []
		for luta in lutas:
			try:
				classe = IdClassePeso.objects.get(id_classe_peso=luta.id_classe_peso)
				normalized.append({
					"luta_id": luta.id,
					"weight_class": classe.peso,
					"atleta1": luta.id_atleta1,
					"atleta2": luta.id_atleta2,
					"resultado": luta.resultado,
				})
			except IdClassePeso.DoesNotExist:
				continue
		return Response(normalized)


class ArenaEventSnapshotView(APIView):
	def get(self, request, arena_event_id):
		serializer = ArenaEventSnapshotRequestSerializer(data=request.query_params)
		serializer.is_valid(raise_exception=True)

		try:
			snapshot = build_event_snapshot(
				credentials_pk=serializer.validated_data["credential_id"],
				arena_event_id=arena_event_id,
				sge_event_id=serializer.validated_data.get("sge_event_id"),
			)
		except ArenaIntegrationError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

		return Response(snapshot)


class ArenaEventRankingSyncView(APIView):
	def post(self, request, arena_event_id):
		serializer = ArenaEventSyncRequestSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		try:
			result = sync_event_rankings_to_sge(
				credentials_pk=serializer.validated_data["credential_id"],
				arena_event_id=arena_event_id,
				sge_event_id=serializer.validated_data.get("sge_event_id"),
			)
		except ArenaIntegrationError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

		return Response(result, status=status.HTTP_200_OK)

