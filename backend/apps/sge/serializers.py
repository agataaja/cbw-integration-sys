"""
Serializers for SGE app models and external API interactions.
"""
from rest_framework import serializers
from .models import ResultadoSGE, LutaSGE


class ResultadoSGESerializer(serializers.ModelSerializer):
    """
    Serializer for ResultadoSGE model (resultado-rank-arena endpoint).
    Handles ranking data from Arena competitions.
    """
    class Meta:
        model = ResultadoSGE
        fields = [
            'id',
            'id_evento',
            'id_evento_arena',
            'sportalternatename',
            'sportname',
            'name',
            'sportid',
            'audiencename',
            'countfighters',
            'countfights',
            'weightcategoryfullname',
            'customid',
            'fullname',
            'rank',
            'id_estabelecimento',
            'id_classe_peso',
            'created_by',
            'updated_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class LutaSGESerializer(serializers.ModelSerializer):
    """
    Serializer for LutaSGE model (evento-luta endpoint).
    Handles fight/bout data from competitions.
    """
    class Meta:
        model = LutaSGE
        fields = [
            'id',
            'id_categoria_arena',
            'id_evento',
            'id_atleta1',
            'id_atleta2',
            'flag_finalizado',
            'round',
            'id_atleta_ganhador',
            'sportAlternateName',
            'weightCategoryName',
            'audienceName',
            'id_classe_peso',
            'atleta1_flag_injured',
            'atleta1_flag_seeded',
            'atleta1_draw_rank',
            'atleta1_RobinRank',
            'atleta2_flag_injured',
            'atleta2_flag_seeded',
            'atleta2_draw_rank',
            'atleta2_RobinRank',
            'resultado',
            'tipo_vitoria',
            'atleta1_ranking_point',
            'atleta2_ranking_point',
            'numero',
            'tapete',
            'data_inicio',
            'data_fim',
            'is_temporary',
        ]
        read_only_fields = ['id']


class BulkOperationRequestSerializer(serializers.Serializer):
    """
    Serializer for bulk operation requests.
    Used to validate event_id parameter for bulk delete/update operations.
    """
    event_id = serializers.IntegerField(
        required=True,
        help_text="SGE event ID to filter records for bulk operations"
    )


class BulkOperationResponseSerializer(serializers.Serializer):
    """
    Serializer for bulk operation responses.
    Returns summary of successful and failed operations.
    """
    success_count = serializers.IntegerField()
    failure_count = serializers.IntegerField()
    total_records = serializers.IntegerField()
    successful_ids = serializers.ListField(child=serializers.CharField())
    failed_operations = serializers.ListField(child=serializers.DictField())
    message = serializers.CharField()
