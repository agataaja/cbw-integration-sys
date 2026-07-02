from rest_framework import serializers
from apps.integration.models import ClientBridge, EventBridge
from apps.sge.models import GestaoEventos
from apps.normalization.models import AgeGroupMapping


class AgeGroupMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgeGroupMapping
        fields = ('id', 'canonical_name', 'arena_variations', 'sge_variations', 'sort_order')


class EventosSgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GestaoEventos
        fields = ('id', 'descricao', 'escopo', 'data_inicio', 'data_fim')


class EventosArenaSerializer(serializers.ModelSerializer):
    sge_event = EventosSgeSerializer(read_only=True)
    age_group_mappings = AgeGroupMappingSerializer(many=True, read_only=True)

    class Meta:
        model = EventBridge
        fields = (
            'id',
            'nome',
            'age_group',
            'sge_age_category',
            'age_group_mappings',
            'arena_event',
            'sge_event',
            'created_at',
        )


class EventosBridgeSerializer(serializers.ModelSerializer):
    age_group_mapping_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=AgeGroupMapping.objects.all(),
        write_only=True,
        required=False,
        source='age_group_mappings',
    )
    
    class Meta:
        model = EventBridge
        fields = (
            'id',
            'nome',
            'age_group',
            'sge_age_category',
            'age_group_mapping_ids',
            'arena_event',
            'sge_event',
            'created_at',
        )
        read_only_fields = ('id', 'created_at')
    
    def create(self, validated_data):
        age_group_mappings = validated_data.pop('age_group_mappings', [])
        instance = super().create(validated_data)
        if age_group_mappings:
            instance.age_group_mappings.set(age_group_mappings)
        return instance
    
    def update(self, instance, validated_data):
        age_group_mappings = validated_data.pop('age_group_mappings', None)
        instance = super().update(instance, validated_data)
        if age_group_mappings is not None:
            instance.age_group_mappings.set(age_group_mappings)
        return instance


class ArenaClientsBridgeSerializer(serializers.ModelSerializer):
    eventos_match = EventosBridgeSerializer(many=True, read_only=True)

    class Meta:
        model = ClientBridge
        fields = ('id', 'arena_client', 'eventos_match', 'created_at')


class ArenaClientsBridgeWriteSerializer(serializers.ModelSerializer):
    eventos_match_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=EventBridge.objects.all(),
        write_only=True,
        required=False,
        source='eventos_match',
    )

    class Meta:
        model = ClientBridge
        fields = ('id', 'arena_client', 'eventos_match_ids', 'created_at')
        read_only_fields = ('id', 'created_at')

    def create(self, validated_data):
        eventos_match = validated_data.pop('eventos_match', [])
        instance = super().create(validated_data)
        if eventos_match:
            instance.eventos_match.set(eventos_match)
        return instance

    def update(self, instance, validated_data):
        eventos_match = validated_data.pop('eventos_match', None)
        instance = super().update(instance, validated_data)
        if eventos_match is not None:
            instance.eventos_match.set(eventos_match)
        return instance


class ArenaEventSnapshotRequestSerializer(serializers.Serializer):
    credential_id = serializers.IntegerField(min_value=1)
    sge_event_id = serializers.IntegerField(min_value=1, required=False)


class ArenaEventSyncRequestSerializer(serializers.Serializer):
    credential_id = serializers.IntegerField(min_value=1)
    sge_event_id = serializers.IntegerField(min_value=1, required=False)


class BridgeCredentialRequestSerializer(serializers.Serializer):
    """Simple serializer for EventBridge custom actions that only need credential_id."""
    credential_id = serializers.IntegerField(min_value=1)
