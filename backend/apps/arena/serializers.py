from rest_framework import serializers

from .models import (
    ArenaClient,
    ArenaFight,
    ArenaFighter,
    ArenaSportEvent,
    ArenaSportEventWeightCategory,
    ArenaWebhookPayload,
    Tunnel, 
)


class ArenaClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArenaClient
        fields = "__all__"


class ArenaWebhookPayloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArenaWebhookPayload
        fields = "__all__"


class ArenaWebhookRequestSerializer(serializers.Serializer):
    entity = serializers.CharField()
    id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    sportEventId = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    audienceName = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class ArenaSportEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArenaSportEvent
        fields = "__all__"


class ArenaSportEventWeightCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ArenaSportEventWeightCategory
        fields = "__all__"


class ArenaFightSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArenaFight
        fields = "__all__"


class ArenaFighterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArenaFighter
        fields = "__all__"


class ArenaClientSyncRequestSerializer(serializers.Serializer):
    arena_client_id = serializers.IntegerField(min_value=1)


class ArenaEventSyncRequestSerializer(serializers.Serializer):
    arena_client_id = serializers.IntegerField(min_value=1)
    arena_event_id = serializers.CharField()


class TunnelRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tunnel
        fields = "__all__"