from rest_framework import serializers

from .models import (
    ArenaClient,
    ArenaFight,
    ArenaFighter,
    ArenaSportEvent,
    ArenaSportEventWeightCategory,)


class ArenaClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArenaClient
        fields = "__all__"


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


