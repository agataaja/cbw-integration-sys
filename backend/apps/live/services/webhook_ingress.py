from __future__ import annotations

from apps.integration.models import ClientBridge, EventBridge
from apps.integration.services import build_event_snapshot, sync_event_rankings_to_sge


def _resolve_binding(payload: dict) -> tuple[str | None, str | None, int | None, int | None]:
    entity = payload.get("entity")
    arena_event_id = payload.get("sportEventId") or payload.get("id")

    if not arena_event_id:
        return entity, None, None, None

    event_match = EventBridge.objects.select_related('sge_event').filter(arena_event__event_id=str(arena_event_id)).first()
    if not event_match:
        return entity, str(arena_event_id), None, None

    client_match = ClientBridge.objects.filter(eventos_match=event_match).select_related("arena_client").first()
    credential_id = client_match.arena_client_id if client_match else None

    sge_event_id = event_match.sge_event_id
    return entity, str(arena_event_id), credential_id, sge_event_id


def ingest_arena_webhook(payload: dict, sge_event_id: int | None = None) -> dict:
    entity, arena_event_id, credential_id, resolved_sge_event_id = _resolve_binding(payload)

    if sge_event_id is None:
        sge_event_id = resolved_sge_event_id

    if not arena_event_id or not credential_id:
        return {
            "status": "ignored",
            "reason": "event_binding_not_found",
            "entity": entity,
            "arena_event_id": arena_event_id,
        }

    if entity in {"SportEvent", "SportEventWeightCategory"}:
        return build_event_snapshot(
            credentials_pk=credential_id,
            arena_event_id=arena_event_id,
            sge_event_id=sge_event_id,
        )

    if entity == "Fight":
        return sync_event_rankings_to_sge(
            credentials_pk=credential_id,
            arena_event_id=arena_event_id,
            sge_event_id=sge_event_id,
        )

    return {
        "status": "ignored",
        "reason": f"unsupported_entity:{entity}",
        "arena_event_id": arena_event_id,
    }


def handle_webhook(payload: dict) -> dict:
    return ingest_arena_webhook(payload)
