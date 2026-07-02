from __future__ import annotations

from apps.integration.models import EventBridge


def get_evento_sge_from_fight(fight_data, sport_event_id=None):
    if not sport_event_id:
        sport_event_id = fight_data.get('sportEventId')

    audience_name = fight_data.get('audienceName')

    if not sport_event_id:
        return None

    event_match = EventBridge.objects.filter(arena_event__event_id=str(sport_event_id)).select_related('sge_event').first()
    if not event_match:
        return None

    eventos_sge = event_match.sge_event.all()
    if not eventos_sge.exists():
        return None

    if audience_name:
        evento_sge = eventos_sge.filter(audienceName__iexact=audience_name).first()
        if evento_sge:
            return evento_sge.id

    if eventos_sge.count() == 1:
        return eventos_sge.first().id

    return None
