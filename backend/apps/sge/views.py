"""
SGE app views for managing ranking and fight data.
Provides CRUD operations for SGE external API endpoints.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import ResultadoSGE, LutaSGE
from .serializers import (
    ResultadoSGESerializer,
    LutaSGESerializer,
    BulkOperationRequestSerializer,
    BulkOperationResponseSerializer,
)
from .services import SGEResultadoService, SGELutaService, SGEServiceError


class ResultadoSGEViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing SGE ranking data (resultado-rank-arena endpoint).
    
    Provides standard CRUD operations plus bulk delete/update based on event_id.
    Note: SGE API only supports individual operations by ID, so bulk operations
    fetch all records by event_id then process each individually.
    """
    queryset = ResultadoSGE.objects.all()
    serializer_class = ResultadoSGESerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'], url_path='by-event/(?P<event_id>[0-9]+)')
    def get_by_event(self, request, event_id=None):
        """
        GET /api/sge/rankings/by-event/{event_id}/
        GET /api/sge/rankings/by-event/{event_id}/?fetch_all=false
        
        Fetch ranking records for a specific event from SGE API.
        By default fetches all pages. Set fetch_all=false to get only first page.
        """
        try:
            fetch_all = request.query_params.get('fetch_all', 'true').lower() == 'true'
            records = SGEResultadoService.get_by_event_id(int(event_id), fetch_all_pages=fetch_all)
            return Response({
                'event_id': event_id,
                'count': len(records),
                'fetched_all_pages': fetch_all,
                'results': records
            })
        except SGEServiceError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            return Response(
                {'error': f'Unexpected error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['delete'], url_path='bulk-delete-by-event')
    def bulk_delete_by_event(self, request):
        """
        DELETE /api/sge/rankings/bulk-delete-by-event/
        
        Delete all ranking records for a specific event.
        Request body: {"event_id": 123}
        
        Returns summary of successful and failed deletions.
        """
        request_serializer = BulkOperationRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(
                request_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        event_id = request_serializer.validated_data['event_id']
        
        try:
            result = SGEResultadoService.bulk_delete_by_event_id(event_id)
            response_serializer = BulkOperationResponseSerializer(result)
            
            # Return 207 Multi-Status if there were partial failures
            response_status = status.HTTP_200_OK
            if result['failure_count'] > 0:
                response_status = status.HTTP_207_MULTI_STATUS
            
            return Response(response_serializer.data, status=response_status)
            
        except SGEServiceError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            return Response(
                {'error': f'Unexpected error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['put'], url_path='bulk-update-by-event')
    def bulk_update_by_event(self, request):
        """
        PUT /api/sge/rankings/bulk-update-by-event/
        
        Update all ranking records for a specific event with provided data.
        Request body: {
            "event_id": 123,
            "updates": {"field1": "value1", "field2": "value2"}
        }
        
        Returns summary of successful and failed updates.
        """
        event_id = request.data.get('event_id')
        updates = request.data.get('updates', {})
        
        if not event_id:
            return Response(
                {'error': 'event_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not updates:
            return Response(
                {'error': 'updates object is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = SGEResultadoService.bulk_update_by_event_id(int(event_id), updates)
            response_serializer = BulkOperationResponseSerializer(result)
            
            # Return 207 Multi-Status if there were partial failures
            response_status = status.HTTP_200_OK
            if result['failure_count'] > 0:
                response_status = status.HTTP_207_MULTI_STATUS
            
            return Response(response_serializer.data, status=response_status)
            
        except SGEServiceError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            return Response(
                {'error': f'Unexpected error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LutaSGEViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing SGE fight/bout data (evento-luta endpoint).
    
    Provides standard CRUD operations plus bulk delete/update based on event_id.
    Note: SGE API only supports individual operations by ID, so bulk operations
    fetch all records by event_id then process each individually.
    """
    queryset = LutaSGE.objects.all()
    serializer_class = LutaSGESerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'], url_path='by-event/(?P<event_id>[0-9]+)')
    def get_by_event(self, request, event_id=None):
        """
        GET /api/sge/fights/by-event/{event_id}/
        GET /api/sge/fights/by-event/{event_id}/?fetch_all=false
        
        Fetch fight records for a specific event from SGE API.
        By default fetches all pages. Set fetch_all=false to get only first page.
        """
        try:
            fetch_all = request.query_params.get('fetch_all', 'true').lower() == 'true'
            records = SGELutaService.get_by_event_id(int(event_id), fetch_all_pages=fetch_all)
            return Response({
                'event_id': event_id,
                'count': len(records),
                'fetched_all_pages': fetch_all,
                'results': records
            })
        except SGEServiceError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            return Response(
                {'error': f'Unexpected error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['delete'], url_path='bulk-delete-by-event')
    def bulk_delete_by_event(self, request):
        """
        DELETE /api/sge/fights/bulk-delete-by-event/
        
        Delete all fight records for a specific event.
        Request body: {"event_id": 123}
        
        Returns summary of successful and failed deletions.
        """
        request_serializer = BulkOperationRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(
                request_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        event_id = request_serializer.validated_data['event_id']
        
        try:
            result = SGELutaService.bulk_delete_by_event_id(event_id)
            response_serializer = BulkOperationResponseSerializer(result)
            
            # Return 207 Multi-Status if there were partial failures
            response_status = status.HTTP_200_OK
            if result['failure_count'] > 0:
                response_status = status.HTTP_207_MULTI_STATUS
            
            return Response(response_serializer.data, status=response_status)
            
        except SGEServiceError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            return Response(
                {'error': f'Unexpected error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['put'], url_path='bulk-update-by-event')
    def bulk_update_by_event(self, request):
        """
        PUT /api/sge/fights/bulk-update-by-event/
        
        Update all fight records for a specific event with provided data.
        Request body: {
            "event_id": 123,
            "updates": {"field1": "value1", "field2": "value2"}
        }
        
        Returns summary of successful and failed updates.
        """
        event_id = request.data.get('event_id')
        updates = request.data.get('updates', {})
        
        if not event_id:
            return Response(
                {'error': 'event_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not updates:
            return Response(
                {'error': 'updates object is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = SGELutaService.bulk_update_by_event_id(int(event_id), updates)
            response_serializer = BulkOperationResponseSerializer(result)
            
            # Return 207 Multi-Status if there were partial failures
            response_status = status.HTTP_200_OK
            if result['failure_count'] > 0:
                response_status = status.HTTP_207_MULTI_STATUS
            
            return Response(response_serializer.data, status=response_status)
            
        except SGEServiceError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            return Response(
                {'error': f'Unexpected error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
