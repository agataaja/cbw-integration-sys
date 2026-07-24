from rest_framework import serializers

from apps.arena.models import (
    ArenaClient,
    ArenaFight,
    ArenaFighter,
    ArenaSportEvent,
    ArenaSportEventWeightCategory,
    ArenaWebhookPayload, 
)

from .models import Tunnel


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



class TunnelRegisterSerializer(serializers.Serializer):
    instance = serializers.CharField(max_length=255)

    status = serializers.ChoiceField(
        choices=Tunnel.Status.choices
    )

    provider = serializers.ChoiceField(
        choices=Tunnel.Provider.choices,
        default=Tunnel.Provider.NGROK,
    )

    public_url = serializers.URLField(
        required=False,
        allow_null=True,
        allow_blank=True,
    )