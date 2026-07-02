from __future__ import annotations

from apps.arena.models import (
    ArenaClient,
    ArenaFight,
    ArenaFighter,
    ArenaSportEvent,
    ArenaSportEventWeightCategory,
)
from apps.arena.services.arena_client import (
    get_all_fights_by_event_id,
    get_all_sport_events_info,
    get_endpoint_response,
    get_headers,
)


def sync_sport_events(arena_client_id: int) -> dict:
    arena_client = ArenaClient.objects.get(pk=arena_client_id)
    response = get_all_sport_events_info(arena_client_id)
    items = response.get("events", {}).get("items", [])

    synced = 0
    for item in items:
        ArenaSportEvent.objects.update_or_create(
            arena_client=arena_client,
            event_id=str(item.get("id")),
            defaults={
                "name": item.get("name") or "",
            },
        )
        synced += 1

    return {"arena_client_id": arena_client_id, "events_synced": synced}


def sync_event_structure(arena_client_id: int, arena_event_id: str) -> dict:
    arena_event = ArenaSportEvent.objects.select_related("arena_client").get(
        arena_client_id=arena_client_id,
        event_id=str(arena_event_id),
    )

    headers = get_headers(arena_client_id)
    categories_response = get_endpoint_response(headers, f"weight-category/{arena_event_id}", pk=arena_client_id)
    categories = categories_response.get("weightCategories", [])

    category_count = 0
    fight_count = 0
    fighter_count = 0

    for category in categories:
        category_obj, _ = ArenaSportEventWeightCategory.objects.update_or_create(
            arena_sport_event=arena_event,
            category_id=str(category.get("id")),
            defaults={"name": category.get("shortName") or category.get("name") or ""},
        )
        category_count += 1

    fights = get_all_fights_by_event_id(arena_event_id, pk=arena_client_id)
    categories_by_id = {
        c.category_id: c
        for c in ArenaSportEventWeightCategory.objects.filter(arena_sport_event=arena_event)
    }

    for fight in fights:
        category_id = str(fight.get("sportEventWeightCategoryId") or "")
        category_obj = categories_by_id.get(category_id)
        if not category_obj:
            continue

        fight_obj, _ = ArenaFight.objects.update_or_create(
            arena_sport_event_weight_category=category_obj,
            fight_id=str(fight.get("id")),
            defaults={"name": f"Fight {fight.get('fightNumber') or ''}".strip()},
        )
        fight_count += 1

        fighter_candidates = [
            (fight.get("fighter1Id"), fight.get("fighter1FullName")),
            (fight.get("fighter2Id"), fight.get("fighter2FullName")),
        ]
        for fighter_id, fighter_name in fighter_candidates:
            if not fighter_id:
                continue
            ArenaFighter.objects.update_or_create(
                fight=fight_obj,
                fighter_id=str(fighter_id),
                defaults={"name": fighter_name or ""},
            )
            fighter_count += 1

    return {
        "arena_client_id": arena_client_id,
        "arena_event_id": str(arena_event_id),
        "categories_synced": category_count,
        "fights_synced": fight_count,
        "fighters_synced": fighter_count,
    }
