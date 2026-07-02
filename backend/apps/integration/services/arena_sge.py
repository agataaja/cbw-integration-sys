import json
from typing import Any
import os
import logging
from datetime import datetime

import requests

from apps.arena.services.arena_client import (
    get_all_fights_by_event_id,
    get_endpoint_response,
    get_headers,
    get_weight_categories_by_sport_event_id,
)
from apps.integration.models import EventBridge
from apps.normalization.models import IdClassePeso
from apps.sge.models import GestaoEventos, GestaoIdsAtletas
from apps.normalization.services.mapping import infer_sport_alternate_name, normalize_audience_name, parse_weight_category

logger = logging.getLogger(__name__)

SGE_RANKING_API_URL = os.getenv("SGE_ARENA_API_URL", "https://restcbw.bigmidia.com/cbw/api") + "/resultado-rank-arena"
SGE_FIGHT_API_URL = os.getenv("SGE_ARENA_API_URL", "https://restcbw.bigmidia.com/cbw/api") + "/evento-luta"
SGE_GESTAO_API_URL = os.getenv("SGE_GESTAO_API_URL", "https://restcbw.bigmidia.com/cbw/gestao")


class ArenaIntegrationError(Exception):
    pass


def _format_datetime_for_mysql(iso_datetime_str: str | None) -> str | None:
    """
    Convert ISO 8601 datetime string to MySQL DATETIME format.
    
    Args:
        iso_datetime_str: ISO format like '2026-05-16T16:26:37-03:00'
    
    Returns:
        MySQL format like '2026-05-16 16:26:37' or None if input is None/empty
    """
    if not iso_datetime_str:
        return None
    
    try:
        # Parse ISO 8601 format (handles timezone)
        dt = datetime.fromisoformat(iso_datetime_str)
        # Format as MySQL DATETIME (no timezone)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, AttributeError) as e:
        logger.warning(f"[_format_datetime_for_mysql] Failed to parse datetime '{iso_datetime_str}': {e}")
        return None


def _iter_ranking_items(ranking_payload: Any) -> list[dict[str, Any]]:
    if isinstance(ranking_payload, dict):
        return list(ranking_payload.values())
    if isinstance(ranking_payload, list):
        return ranking_payload
    return []


def _resolve_event_binding(arena_event_id: str) -> EventBridge:
    try:
        return EventBridge.objects.select_related("arena_event", "sge_event").get(
            arena_event__event_id=str(arena_event_id)
        )
    except EventBridge.DoesNotExist as exc:
        raise ArenaIntegrationError(
            f"Arena event {arena_event_id} is not registered in integration match table."
        ) from exc


def _resolve_mapping_for_age_group(arena_event_id: str, age_group: str) -> EventBridge | None:
    queryset = EventBridge.objects.select_related('sge_event', 'arena_event').filter(
        arena_event__event_id=str(arena_event_id)
    )

    if age_group:
        scoped = queryset.filter(age_group__iexact=age_group)
        if scoped.exists():
            return scoped.first()

    return queryset.first()


def _resolve_sge_event_id(event_match: EventBridge | None, explicit_sge_event_id: int | None) -> int | None:
    if explicit_sge_event_id:
        return explicit_sge_event_id

    if not event_match or not event_match.sge_event_id:
        return None

    return event_match.sge_event_id


def _resolve_id_classe_peso(evento_sge: GestaoEventos | None, parsed_category: dict[str, str]) -> int | None:
    filters = {
        "estilo__iexact": parsed_category["sport_alternate_name"],
        "categoria__iexact": parsed_category["weight_name"],
    }

    if evento_sge and evento_sge.data_fim:
        filters["ano"] = str(evento_sge.data_fim)[:4]
    if evento_sge and evento_sge.escopo:
        filters["escopo__iexact"] = evento_sge.escopo
    elif parsed_category["audience_name"]:
        filters["escopo__iexact"] = parsed_category["audience_name"]

    match = IdClassePeso.objects.filter(**filters).values_list("id_classe_peso", flat=True).first()
    return match


def _get_person_custom_id(headers: dict[str, str], credentials_pk: int, person_id: Any, cache: dict[str, str]) -> str:
    cache_key = str(person_id)
    if cache_key in cache:
        return cache[cache_key]

    response = get_endpoint_response(headers, f"person/get/{person_id}", pk=credentials_pk)
    custom_id = str(response.get("person", {}).get("customId") or "")
    cache[cache_key] = custom_id
    return custom_id


def _build_rankings(credentials_pk: int, arena_event_id: str, age_group: str | None = None, explicit_sge_event_id: int | None = None) -> list[dict[str, Any]]:
    headers = get_headers(credentials_pk)
    _resolve_event_binding(arena_event_id)
    
    # Use dedicated arena_client function to get weight categories
    weight_categories_dict = get_weight_categories_by_sport_event_id(arena_event_id, pk=credentials_pk)
    
    # Get EventBridge mappings with prefetched age_group_mappings
    event_bridges = EventBridge.objects.select_related('sge_event', 'arena_event').prefetch_related('age_group_mappings').filter(
        arena_event__event_id=str(arena_event_id)
    )
    
    # If age_group filter is specified, narrow down to that mapping
    if age_group:
        event_bridges = event_bridges.filter(age_group__iexact=age_group)
    
    # Build a mapping of normalized age groups to EventBridge and SGE variation
    # Key: uppercase arena variation, Value: (EventBridge, primary_sge_variation, age_group_mapping)
    age_group_lookup = {}
    for bridge in event_bridges:
        for age_mapping in bridge.age_group_mappings.all():
            for arena_var in age_mapping.arena_variations:
                age_group_lookup[arena_var.upper().strip()] = (bridge, age_mapping.primary_sge_variation, age_mapping)
        
        # Fallback: if bridge has legacy age_group string and no mappings, use that
        if not bridge.age_group_mappings.exists() and bridge.age_group:
            age_group_lookup[bridge.age_group.upper().strip()] = (
                bridge, 
                bridge.sge_age_category or bridge.age_group,
                None
            )
    
    person_cache: dict[str, str] = {}
    payloads: list[dict[str, Any]] = []

    for category_id, category_short_name in weight_categories_dict.items():
        # Parse category name to extract age group
        parsed_category = parse_weight_category(category_short_name)
        category_audience = parsed_category["audience_name"].upper().strip() if parsed_category["audience_name"] else ""
        
        # Look up the matching EventBridge and SGE variation
        match_info = age_group_lookup.get(category_audience)
        
        if not match_info:
            # No mapping found for this age group - skip
            continue
        
        bridge, sge_variation, age_mapping = match_info
        
        ranking_response = get_endpoint_response(
            headers,
            f"weight-category/get/{category_id}/ranking?=",
            pk=credentials_pk,
        )
        ranking_items = _iter_ranking_items(ranking_response.get("ranking"))

        for item in ranking_items:
            fighter = item.get("fighter", {})
            weight_category_full_name = fighter.get("weightCategoryFullName") or category_short_name or ""
            
            # Use the resolved SGE event and variation from the matched bridge
            sge_event_id = _resolve_sge_event_id(bridge, explicit_sge_event_id)
            matching_sge_event = bridge.sge_event if bridge.sge_event_id else None
            
            custom_id = ""
            person_id = fighter.get("personId")
            if person_id:
                custom_id = _get_person_custom_id(headers, credentials_pk, person_id, person_cache)

            payloads.append({
                "id_evento": sge_event_id,
                "id_evento_arena": str(fighter.get("sportEventId") or arena_event_id),
                "countFighters": str(fighter.get("weightCategoryCountReadyFighters") or ""),
                "countFights": str(fighter.get("weightCategoryCountFights") or ""),
                "weightCategoryFullName": weight_category_full_name,
                "customId": custom_id,
                "fullName": str(fighter.get("fullName") or ""),
                "rank": str(fighter.get("rank") or ""),
                "sportAlternateName": infer_sport_alternate_name(parsed_category["sport_name"]),
                "sportName": parsed_category["sport_name"],
                "name": parsed_category["weight_name"],
                "audienceName": sge_variation,  # Use the normalized SGE variation
                "id_classe_peso": _resolve_id_classe_peso(matching_sge_event, parsed_category),
                "source_category_id": category_id,
                "match_id": bridge.id,
                "age_group_mapping_id": age_mapping.id if age_mapping else None,
            })

    return payloads


def _build_fights(credentials_pk: int, arena_event_id: str) -> list[dict[str, Any]]:
    headers = get_headers(credentials_pk)
    fights = get_all_fights_by_event_id(arena_event_id, pk=credentials_pk)
    person_cache: dict[str, str] = {}
    results = []

    for fight in fights:
        fighter1_custom_id = ""
        fighter2_custom_id = ""

        if fight.get("fighter1PersonId"):
            fighter1_custom_id = _get_person_custom_id(headers, credentials_pk, fight["fighter1PersonId"], person_cache)
        if fight.get("fighter2PersonId"):
            fighter2_custom_id = _get_person_custom_id(headers, credentials_pk, fight["fighter2PersonId"], person_cache)

        results.append({
            "fight_id": fight.get("id"),
            "fight_number": fight.get("fightNumber"),
            "winner_fighter_id": fight.get("winnerFighter"),
            "result": fight.get("result"),
            "victory_type": fight.get("victoryType"),
            "ranking_point_nice_name": fight.get("rankingPointNiceName"),
            "weight_category_id": fight.get("sportEventWeightCategoryId"),
            "weight_category_name": fight.get("weightCategoryFullName"),
            "fighter1_name": fight.get("fighter1FullName"),
            "fighter1_custom_id": fighter1_custom_id,
            "fighter2_name": fight.get("fighter2FullName"),
            "fighter2_custom_id": fighter2_custom_id,
            "team1": fight.get("team1AlternateName"),
            "team2": fight.get("team2AlternateName"),
            "end_time": fight.get("endTime"),
        })

    return results


def _build_rankings_for_bridge(credentials_pk: int, event_bridge_id: int) -> list[dict[str, Any]]:
    """
    Build ranking payloads for a specific EventBridge.
    Uses the bridge's arena_event, sge_event, and age_group_mappings directly.
    """
    logger.info(f"[_build_rankings_for_bridge] Starting for event_bridge_id={event_bridge_id}, credentials_pk={credentials_pk}")
    
    try:
        bridge = EventBridge.objects.select_related('arena_event', 'sge_event').prefetch_related('age_group_mappings').get(id=event_bridge_id)
        logger.info(f"[_build_rankings_for_bridge] Found EventBridge: id={bridge.id}, nome={bridge.nome}")
    except EventBridge.DoesNotExist as exc:
        logger.error(f"[_build_rankings_for_bridge] EventBridge {event_bridge_id} not found")
        raise ArenaIntegrationError(f"EventBridge with ID {event_bridge_id} not found.") from exc
    
    if not bridge.arena_event:
        logger.error(f"[_build_rankings_for_bridge] EventBridge {event_bridge_id} has no arena_event")
        raise ArenaIntegrationError(f"EventBridge {event_bridge_id} has no associated Arena event.")
    
    arena_event_id = bridge.arena_event.event_id
    sge_event_id = bridge.sge_event.id if bridge.sge_event else None
    logger.info(f"[_build_rankings_for_bridge] arena_event_id={arena_event_id}, sge_event_id={sge_event_id}")
    
    headers = get_headers(credentials_pk)
    weight_categories_dict = get_weight_categories_by_sport_event_id(arena_event_id, pk=credentials_pk)
    logger.info(f"[_build_rankings_for_bridge] Retrieved {len(weight_categories_dict)} weight categories from Arena")
    logger.debug(f"[_build_rankings_for_bridge] Weight categories: {weight_categories_dict}")
    
    # Build lookup for this bridge's age group mappings
    age_group_mappings = bridge.age_group_mappings.all()
    logger.info(f"[_build_rankings_for_bridge] Bridge has {age_group_mappings.count()} age_group_mappings")
    
    age_group_lookup = {}
    for age_mapping in age_group_mappings:
        primary_sge_variation = age_mapping.primary_sge_variation
        logger.debug(f"[_build_rankings_for_bridge] Processing age_mapping: canonical_name={age_mapping.canonical_name}, primary_sge={primary_sge_variation}, arena_variations={age_mapping.arena_variations}")
        for arena_var in age_mapping.arena_variations:
            age_group_lookup[arena_var.upper().strip()] = (primary_sge_variation, age_mapping)
    
    # Fallback: legacy age_group field if no mappings exist
    if not age_group_lookup and bridge.age_group:
        logger.info(f"[_build_rankings_for_bridge] Using legacy age_group field: {bridge.age_group}")
        age_group_lookup[bridge.age_group.upper().strip()] = (
            bridge.sge_age_category or bridge.age_group,
            None
        )
    
    logger.info(f"[_build_rankings_for_bridge] Built age_group_lookup with {len(age_group_lookup)} entries")
    logger.debug(f"[_build_rankings_for_bridge] age_group_lookup keys: {list(age_group_lookup.keys())}")
    
    person_cache: dict[str, str] = {}
    payloads: list[dict[str, Any]] = []
    
    for category_id, category_short_name in weight_categories_dict.items():
        logger.debug(f"[_build_rankings_for_bridge] Processing category: id={category_id}, name={category_short_name}")
        
        parsed_category = parse_weight_category(category_short_name)
        category_audience = parsed_category["audience_name"].upper().strip() if parsed_category["audience_name"] else ""
        logger.debug(f"[_build_rankings_for_bridge] Parsed category: sport={parsed_category['sport_name']}, weight={parsed_category['weight_name']}, audience='{category_audience}'")
        
        # Check if this category matches any of the bridge's age groups
        match_info = age_group_lookup.get(category_audience)
        if not match_info:
            logger.warning(f"[_build_rankings_for_bridge] No age group match for category '{category_short_name}' (audience='{category_audience}'). Skipping.")
            continue
        
        sge_variation, age_mapping = match_info
        logger.info(f"[_build_rankings_for_bridge] Matched category '{category_short_name}' to age_group mapping (canonical={age_mapping.canonical_name if age_mapping else 'legacy'}, sge_variation={sge_variation})")
        
        ranking_response = get_endpoint_response(
            headers,
            f"weight-category/get/{category_id}/ranking?=",
            pk=credentials_pk,
        )
        ranking_items = _iter_ranking_items(ranking_response.get("ranking"))
        logger.info(f"[_build_rankings_for_bridge] Category {category_id} has {len(ranking_items)} ranking items")
        
        for item in ranking_items:
            fighter = item.get("fighter", {})
            weight_category_full_name = fighter.get("weightCategoryFullName") or category_short_name or ""
            
            custom_id = ""
            person_id = fighter.get("personId")
            if person_id:
                custom_id = _get_person_custom_id(headers, credentials_pk, person_id, person_cache)
            
            if fighter.get("isNotRanked") == True: 

                logger.info(f"[_build_rankings_for_bridge] Skipping unranked fighter {fighter.get('fullName')} (custom_id={custom_id}) in category '{category_short_name}'")
                continue
            
            payloads.append({
                "id_evento": sge_event_id,
                "id_evento_arena": str(fighter.get("sportEventId") or arena_event_id),
                "countFighters": str(fighter.get("weightCategoryCountReadyFighters") or ""),
                "countFights": str(fighter.get("weightCategoryCountFights") or ""),
                "weightCategoryFullName": weight_category_full_name,
                "customId": custom_id,
                "fullName": str(fighter.get("fullName") or ""),
                "rank": str(fighter.get("rank") or ""),
                "sportAlternateName": infer_sport_alternate_name(parsed_category["sport_name"]),
                "sportName": parsed_category["sport_name"],
                "name": parsed_category["weight_name"],
                "audienceName": sge_variation,
                "id_classe_peso": _resolve_id_classe_peso(bridge.sge_event, parsed_category),
                "source_category_id": category_id,
                "match_id": bridge.id,
                "age_group_mapping_id": age_mapping.id if age_mapping else None,
            })
    
    logger.info(f"[_build_rankings_for_bridge] Completed. Built {len(payloads)} ranking payloads")
    return payloads


def build_event_snapshot(credentials_pk: int, arena_event_id: str, sge_event_id: int | None = None) -> dict[str, Any]:
    """Legacy function for backward compatibility. Uses arena_event_id lookup."""
    rankings = _build_rankings(credentials_pk, arena_event_id, explicit_sge_event_id=sge_event_id)
    fights = _build_fights(credentials_pk, arena_event_id)
    unresolved_rankings = [item for item in rankings if not item["id_evento"]]

    return {
        "arena_event_id": str(arena_event_id),
        "rankings": rankings,
        "fights": fights,
        "unresolved_rankings": unresolved_rankings,
    }


def build_bridge_snapshot(credentials_pk: int, event_bridge_id: int) -> dict[str, Any]:
    """
    Build snapshot for a specific EventBridge.
    Uses the bridge's relationships directly without arena_event_id lookup.
    """
    try:
        bridge = EventBridge.objects.select_related('arena_event').get(id=event_bridge_id)
    except EventBridge.DoesNotExist as exc:
        raise ArenaIntegrationError(f"EventBridge with ID {event_bridge_id} not found.") from exc
    
    arena_event_id = bridge.arena_event.event_id if bridge.arena_event else None
    if not arena_event_id:
        raise ArenaIntegrationError(f"EventBridge {event_bridge_id} has no associated Arena event.")
    
    rankings = _build_rankings_for_bridge(credentials_pk, event_bridge_id)
    fights = _build_fights(credentials_pk, arena_event_id)
    unresolved_rankings = [item for item in rankings if not item["id_evento"]]
    
    return {
        "event_bridge_id": event_bridge_id,
        "arena_event_id": str(arena_event_id),
        "sge_event_id": bridge.sge_event.id if bridge.sge_event else None,
        "rankings": rankings,
        "fights": fights,
        "unresolved_rankings": unresolved_rankings,
    }


def sync_event_rankings_to_sge(credentials_pk: int, arena_event_id: str, sge_event_id: int | None = None) -> dict[str, Any]:
    """Legacy function for backward compatibility. Uses arena_event_id lookup."""
    rankings = _build_rankings(credentials_pk, arena_event_id, explicit_sge_event_id=sge_event_id)
    synced = []
    skipped = []

    for payload in rankings:
        if not payload["id_evento"]:
            skipped.append({
                "reason": "missing_sge_event_mapping",
                "payload": payload,
            })
            continue

        response = requests.post(
            SGE_RANKING_API_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        synced.append({
            "status_code": response.status_code,
            "payload": payload,
            "response_text": response.text,
        })

    return {
        "arena_event_id": str(arena_event_id),
        "sent": len(synced),
        "skipped": len(skipped),
        "responses": synced,
        "skipped_items": skipped,
    }


def sync_bridge_rankings_to_sge(credentials_pk: int, event_bridge_id: int) -> dict[str, Any]:
    """
    Sync rankings to SGE for a specific EventBridge.
    Uses the bridge's relationships directly without lookup logic.
    """
    logger.info(f"[sync_bridge_rankings_to_sge] Starting sync for event_bridge_id={event_bridge_id}, credentials_pk={credentials_pk}")
    
    try:
        bridge = EventBridge.objects.select_related('arena_event', 'sge_event').get(id=event_bridge_id)
        logger.info(f"[sync_bridge_rankings_to_sge] Found EventBridge: id={bridge.id}, nome={bridge.nome}, sge_event_id={bridge.sge_event.id if bridge.sge_event else None}")
    except EventBridge.DoesNotExist as exc:
        logger.error(f"[sync_bridge_rankings_to_sge] EventBridge {event_bridge_id} not found")
        raise ArenaIntegrationError(f"EventBridge with ID {event_bridge_id} not found.") from exc
    
    if not bridge.sge_event:
        logger.error(f"[sync_bridge_rankings_to_sge] EventBridge {event_bridge_id} has no sge_event")
        raise ArenaIntegrationError(f"EventBridge {event_bridge_id} has no associated SGE event. Cannot sync rankings.")
    
    rankings = _build_rankings_for_bridge(credentials_pk, event_bridge_id)
    logger.info(f"[sync_bridge_rankings_to_sge] Received {len(rankings)} ranking payloads from _build_rankings_for_bridge")
    
    synced = []
    skipped = []
    
    for payload in rankings:
        if not payload["id_evento"]:
            logger.warning(f"[sync_bridge_rankings_to_sge] Skipping payload with missing id_evento: {payload.get('fullName')}")
            skipped.append({
                "reason": "missing_sge_event_mapping",
                "payload": payload,
            })
            continue
        
        logger.debug(f"[sync_bridge_rankings_to_sge] POSTing ranking for {payload.get('fullName')} to {SGE_RANKING_API_URL}")
        response = requests.post(
            SGE_RANKING_API_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        logger.info(f"[sync_bridge_rankings_to_sge] Response for {payload.get('fullName')}: status={response.status_code}")
        synced.append({
            "status_code": response.status_code,
            "payload": payload,
            "response_text": response.text,
        })
    
    logger.info(f"[sync_bridge_rankings_to_sge] Sync completed. sent={len(synced)}, skipped={len(skipped)}")
    
    return {
        "event_bridge_id": event_bridge_id,
        "arena_event_id": str(bridge.arena_event.event_id) if bridge.arena_event else None,
        "sge_event_id": bridge.sge_event.id,
        "sent": len(synced),
        "skipped": len(skipped),
        "responses": synced,
        "skipped_items": skipped,
    }


def _resolve_gestao_ids_atleta(custom_id: str) -> int | None:
    """
    Map Arena custom_id to GestaoIdsAtletas.id.
    
    Arena custom_id → GestaoAtletas.id (via id_atleta FK) → GestaoIdsAtletas.id (PK we need)
    """
    if not custom_id:
        return None
    
    try:
        custom_id_int = int(custom_id)
    except (ValueError, TypeError):
        logger.warning(f"[_resolve_gestao_ids_atleta] Invalid custom_id: {custom_id}")
        return None
    
    # Find GestaoIdsAtletas where id_atleta points to the athlete with this custom_id
    gestao_id = GestaoIdsAtletas.objects.filter(id_atleta=custom_id_int).values_list('id', flat=True).first()
    
    if not gestao_id:
        logger.warning(f"[_resolve_gestao_ids_atleta] No GestaoIdsAtletas found for custom_id={custom_id}")
    
    return gestao_id


def _build_fights_for_bridge(credentials_pk: int, event_bridge_id: int) -> list[dict[str, Any]]:
    """
    Build fight payloads for a specific EventBridge.
    Filters fights by the bridge's age_group_mappings.
    Maps custom_id to GestaoIdsAtletas.id for SGE compatibility.
    """
    logger.info(f"[_build_fights_for_bridge] Starting for event_bridge_id={event_bridge_id}, credentials_pk={credentials_pk}")
    
    try:
        bridge = EventBridge.objects.select_related('arena_event', 'sge_event').prefetch_related('age_group_mappings').get(id=event_bridge_id)
        logger.info(f"[_build_fights_for_bridge] Found EventBridge: id={bridge.id}, nome={bridge.nome}")
    except EventBridge.DoesNotExist as exc:
        logger.error(f"[_build_fights_for_bridge] EventBridge {event_bridge_id} not found")
        raise ArenaIntegrationError(f"EventBridge with ID {event_bridge_id} not found.") from exc
    
    if not bridge.arena_event:
        logger.error(f"[_build_fights_for_bridge] EventBridge {event_bridge_id} has no arena_event")
        raise ArenaIntegrationError(f"EventBridge {event_bridge_id} has no associated Arena event.")
    
    arena_event_id = bridge.arena_event.event_id
    sge_event_id = bridge.sge_event.id if bridge.sge_event else None
    logger.info(f"[_build_fights_for_bridge] arena_event_id={arena_event_id}, sge_event_id={sge_event_id}")
    
    # Build age group lookup for filtering
    age_group_mappings = bridge.age_group_mappings.all()
    logger.info(f"[_build_fights_for_bridge] Bridge has {age_group_mappings.count()} age_group_mappings")
    
    age_group_lookup = {}
    for age_mapping in age_group_mappings:
        primary_sge_variation = age_mapping.primary_sge_variation
        for arena_var in age_mapping.arena_variations:
            age_group_lookup[arena_var.upper().strip()] = (primary_sge_variation, age_mapping)
    
    if not age_group_lookup and bridge.age_group:
        logger.info(f"[_build_fights_for_bridge] Using legacy age_group field: {bridge.age_group}")
        age_group_lookup[bridge.age_group.upper().strip()] = (
            bridge.sge_age_category or bridge.age_group,
            None
        )
    
    logger.info(f"[_build_fights_for_bridge] Built age_group_lookup with {len(age_group_lookup)} entries")
    logger.debug(f"[_build_fights_for_bridge] age_group_lookup keys: {list(age_group_lookup.keys())}")
    
    # Fetch fights from Arena API
    headers = get_headers(credentials_pk)
    fights = get_all_fights_by_event_id(arena_event_id, pk=credentials_pk)
    logger.info(f"[_build_fights_for_bridge] Retrieved {len(fights)} fights from Arena")
    
    person_cache: dict[str, str] = {}
    payloads: list[dict[str, Any]] = []
    
    for fight in fights:
        fight_id = fight.get("id")
        weight_category_name = fight.get("weightCategoryFullName") or ""
        
        logger.debug(f"[_build_fights_for_bridge] Processing fight: id={fight_id}, category={weight_category_name}")
        
        # Parse category to extract age group
        parsed_category = parse_weight_category(weight_category_name)
        category_audience = parsed_category["audience_name"].upper().strip() if parsed_category["audience_name"] else ""
        
        logger.debug(f"[_build_fights_for_bridge] Parsed fight category: sport={parsed_category['sport_name']}, weight={parsed_category['weight_name']}, audience='{category_audience}'")
        
        # Check if this fight matches the bridge's age groups
        match_info = age_group_lookup.get(category_audience)
        if not match_info:
            logger.warning(f"[_build_fights_for_bridge] No age group match for fight {fight_id}, category '{weight_category_name}' (audience='{category_audience}'). Skipping.")
            continue
        
        sge_variation, age_mapping = match_info
        logger.info(f"[_build_fights_for_bridge] Matched fight {fight_id} to age_group (canonical={age_mapping.canonical_name if age_mapping else 'legacy'}, sge_variation={sge_variation})")
        
        # Get person IDs directly from Arena fight response
        fighter1_person_id = fight.get("fighter1PersonId")
        fighter2_person_id = fight.get("fighter2PersonId")
        
        # Initialize athlete IDs as None (for incomplete fights)
        id_atleta1 = None
        id_atleta2 = None
        
        # Try to resolve athlete IDs if person IDs are available
        if fighter1_person_id:
            fighter1_custom_id = _get_person_custom_id(headers, credentials_pk, fighter1_person_id, person_cache)
            # id_atleta1 = _resolve_gestao_ids_atleta(fighter1_custom_id)

            id_atleta1 = fighter1_custom_id

            if not id_atleta1:
                logger.warning(f"[_build_fights_for_bridge] Fight {fight_id}: No GestaoIdsAtletas mapping for fighter1 (custom_id={fighter1_custom_id})")
        else:
            logger.info(f"[_build_fights_for_bridge] Fight {fight_id}: No fighter1PersonId - fight not yet assigned")
        
        if fighter2_person_id:
            fighter2_custom_id = _get_person_custom_id(headers, credentials_pk, fighter2_person_id, person_cache)
            # id_atleta2 = _resolve_gestao_ids_atleta(fighter2_custom_id)
            id_atleta2 = fighter2_custom_id
            if not id_atleta2:
                logger.warning(f"[_build_fights_for_bridge] Fight {fight_id}: No GestaoIdsAtletas mapping for fighter2 (custom_id={fighter2_custom_id})")
        else:
            logger.info(f"[_build_fights_for_bridge] Fight {fight_id}: No fighter2PersonId - fight not yet assigned")
        
        # Determine winner by comparing fighter IDs
        winner_fighter_uuid = fight.get("winnerFighter")
        fighter1_uuid = fight.get("fighter1")
        fighter2_uuid = fight.get("fighter2")
        
        id_atleta_ganhador = None
        if winner_fighter_uuid and id_atleta1 and id_atleta2:
            if winner_fighter_uuid == fighter1_uuid:
                id_atleta_ganhador = id_atleta1
                logger.debug(f"[_build_fights_for_bridge] Fight {fight_id}: Winner is fighter1 (id_atleta={id_atleta1})")
            elif winner_fighter_uuid == fighter2_uuid:
                id_atleta_ganhador = id_atleta2
                logger.debug(f"[_build_fights_for_bridge] Fight {fight_id}: Winner is fighter2 (id_atleta={id_atleta2})")
            else:
                logger.warning(f"[_build_fights_for_bridge] Fight {fight_id}: Winner fighter UUID '{winner_fighter_uuid}' doesn't match fighter1 '{fighter1_uuid}' or fighter2 '{fighter2_uuid}'")
        else:
            logger.debug(f"[_build_fights_for_bridge] Fight {fight_id}: No winner determined yet (incomplete fight)")
        
        # Resolve id_classe_peso
        id_classe_peso = _resolve_id_classe_peso(bridge.sge_event, parsed_category)
        
        # Build payload matching LutaSGE model exactly
        payload = {
            # Primary key and identifiers
            "id": f"{fight_id}_{sge_event_id}",  # Composite key as per LutaSGE model
            "id_categoria_arena": fight.get("sportEventWeightCategoryId"),
            "id_evento": sge_event_id,
            
            # Athletes
            "id_atleta1": id_atleta1,
            "id_atleta2": id_atleta2,
            "id_atleta_ganhador": id_atleta_ganhador,
            
            # Fight metadata
            "flag_finalizado": 1 if fight.get("isCompleted") else 0,
            "round": str(fight.get("round") or fight.get("roundFriendlyName")),
            "numero": fight.get("fightNumber"),
            "tapete": str(fight.get("matName") or "1"),
            
            # Category information
            "sportAlternateName": parsed_category["sport_alternate_name"],
            "weightCategoryName": parsed_category["weight_name"],
            "audienceName": sge_variation,
            "id_classe_peso": id_classe_peso,
            
            # Athlete 1 details
            "atleta1_flag_injured": 1 if fight.get("fighter1IsInjured") else 0,
            "atleta1_flag_seeded": 1 if fight.get("fighter1IsSeeded") else 0,
            "atleta1_draw_rank": str(fight.get("fighter1DrawRank") or ""),
            "atleta1_RobinRank": str(fight.get("fighter1RobinRank") or ""),
            
            # Athlete 2 details
            "atleta2_flag_injured": 1 if fight.get("fighter2IsInjured") else 0,
            "atleta2_flag_seeded": 1 if fight.get("fighter2IsSeeded") else 0,
            "atleta2_draw_rank": str(fight.get("fighter2DrawRank") or ""),
            "atleta2_RobinRank": str(fight.get("fighter2RobinRank") or ""),
            
            # Result information
            "resultado": fight.get("result"),
            "tipo_vitoria": fight.get("victoryType"),
            "atleta1_ranking_point": fight.get("fighter1RankingPoint"),
            "atleta2_ranking_point": fight.get("fighter2RankingPoint"),
            
            # Timestamps - convert ISO 8601 to MySQL DATETIME format
            "data_inicio": _format_datetime_for_mysql(fight.get("expectedStartDate")),
            "data_fim": _format_datetime_for_mysql(fight.get("endDate") or fight.get("completedDate")),
            
            # Additional flags
            "is_temporary": False,
        }
        
        # Log if this is an incomplete fight
        if not id_atleta1 or not id_atleta2:
            logger.info(f"[_build_fights_for_bridge] Fight {fight_id} is incomplete (id_atleta1={id_atleta1}, id_atleta2={id_atleta2}) - will sync with null values")
        
        logger.debug(f"[_build_fights_for_bridge] Built payload for fight {fight_id}: winner={id_atleta_ganhador}, atleta1={id_atleta1}, atleta2={id_atleta2}")
        payloads.append(payload)
    
    logger.info(f"[_build_fights_for_bridge] Completed. Built {len(payloads)} fight payloads")
    return payloads


def sync_bridge_fights_to_sge(credentials_pk: int, event_bridge_id: int) -> dict[str, Any]:
    """
    Sync fights to SGE for a specific EventBridge.
    Uses the bridge's relationships directly without lookup logic.
    """
    logger.info(f"[sync_bridge_fights_to_sge] Starting sync for event_bridge_id={event_bridge_id}, credentials_pk={credentials_pk}")
    
    try:
        bridge = EventBridge.objects.select_related('arena_event', 'sge_event').get(id=event_bridge_id)
        logger.info(f"[sync_bridge_fights_to_sge] Found EventBridge: id={bridge.id}, nome={bridge.nome}, sge_event_id={bridge.sge_event.id if bridge.sge_event else None}")
    except EventBridge.DoesNotExist as exc:
        logger.error(f"[sync_bridge_fights_to_sge] EventBridge {event_bridge_id} not found")
        raise ArenaIntegrationError(f"EventBridge with ID {event_bridge_id} not found.") from exc
    
    if not bridge.sge_event:
        logger.error(f"[sync_bridge_fights_to_sge] EventBridge {event_bridge_id} has no sge_event")
        raise ArenaIntegrationError(f"EventBridge {event_bridge_id} has no associated SGE event. Cannot sync fights.")
    
    fights = _build_fights_for_bridge(credentials_pk, event_bridge_id)
    logger.info(f"[sync_bridge_fights_to_sge] Received {len(fights)} fight payloads from _build_fights_for_bridge")
    
    # Log first payload for debugging
    if fights:
        logger.debug(f"[sync_bridge_fights_to_sge] Sample payload (first fight): {json.dumps(fights[0], indent=2, default=str)}")
    
    synced = []
    skipped = []
    
    for payload in fights:
        if not payload.get("id_evento"):
            logger.warning(f"[sync_bridge_fights_to_sge] Skipping fight with missing id_evento: {payload.get('id')}")
            skipped.append({
                "reason": "missing_sge_event_mapping",
                "payload": payload,
            })
            continue
        
        logger.debug(f"[sync_bridge_fights_to_sge] POSTing fight {payload.get('id')} to {SGE_FIGHT_API_URL}")
        logger.debug(f"[sync_bridge_fights_to_sge] Payload: {json.dumps(payload, default=str)}")
        response = requests.post(
            SGE_FIGHT_API_URL,
            data=json.dumps(payload, default=str),  # Added default=str to handle any non-serializable objects
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        logger.info(f"[sync_bridge_fights_to_sge] Response for fight {payload.get('id')}: status={response.status_code}, text={response.text[:200]}")
        synced.append({
            "status_code": response.status_code,
            "payload": payload,
            "response_text": response.text,
        })
    
    logger.info(f"[sync_bridge_fights_to_sge] Sync completed. sent={len(synced)}, skipped={len(skipped)}")
    
    return {
        "event_bridge_id": event_bridge_id,
        "arena_event_id": str(bridge.arena_event.event_id) if bridge.arena_event else None,
        "sge_event_id": bridge.sge_event.id,
        "sent": len(synced),
        "skipped": len(skipped),
        "responses": synced,
        "skipped_items": skipped,
    }
