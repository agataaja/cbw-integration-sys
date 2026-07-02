from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AgeGroupMapping
from rest_framework import serializers


class AgeGroupMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgeGroupMapping
        fields = '__all__'


class AgeGroupMappingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing age group mappings between Arena and SGE.
    
    Provides CRUD operations for age group normalization tables.
    """
    queryset = AgeGroupMapping.objects.all().order_by('sort_order', 'canonical_name')
    serializer_class = AgeGroupMappingSerializer
    
    @action(detail=False, methods=['post'])
    def populate_defaults(self, request):
        """Populate default age group mappings."""
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('populate_age_groups', stdout=out)
        
        return Response({
            'message': 'Age group mappings populated',
            'output': out.getvalue(),
            'total': AgeGroupMapping.objects.count()
        })
