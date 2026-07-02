# Integration App — Documentation Index
App: integration  
Last documented: May 20, 2026

## Overview

The **integration** app is the cross-domain bridge layer between **Arena** (external competition management platform) and **SGE** (internal sports governance engine). It provides:

1. **Bridge models** — Many-to-many and one-to-many mappings between Arena and SGE entities (events, clients, athletes, fights), with age-group segmentation support.
2. **CRUD endpoints** — Manual management of event/client bridges via DRF ViewSets.
3. **Orchestration services** — Fetch Arena rankings/fights, map to SGE payloads, and sync to SGE REST API.
4. **Read-only endpoints** — Browse event bridges, SGE eventos, and normalized rankings.

---

## Documentation Files

| File | Contents |
|------|----------|
| [models.md](models.md) | Bridge models (`EventBridge`, `ClientBridge`, `AthleteBridge`, `FightBridge`): fields, constraints, relationships, domain meaning. |
| [serializers.md](serializers.md) | Request/response shapes for bridge CRUD, snapshot/sync endpoints: read vs write serializers, nested structures, M2M handling. |
| [views_and_urls.md](views_and_urls.md) | Endpoints table, HTTP methods, query parameters, request/response examples, ViewSet/APIView behavior. |
| [services.md](services.md) | Business logic orchestration: `build_event_snapshot`, `sync_event_rankings_to_sge`, ranking/fight payload construction, mapping resolution. |
| [cross_app_dependencies.md](cross_app_dependencies.md) | Inter-app coupling map: dependencies on `arena`, `sge`, `normalization`; reverse dependency from `arena.webhook`. |
| [external_integrations.md](external_integrations.md) | HTTP contracts: Arena API endpoints (OAuth, weight categories, rankings, fights), SGE ranking sync endpoint, webhook flow. |
| [AGE_GROUP_MAPPING_GUIDE.md](AGE_GROUP_MAPPING_GUIDE.md) | **NEW**: Comprehensive guide to the age group mapping system for handling Arena-SGE age category variations. |

---

## Quick Reference

### Models Summary

| Model | Purpose | Key Relationships |
|-------|---------|-------------------|
| `EventBridge` | Maps Arena event + age group → SGE evento. | `arena_event` (FK), `sge_event` (FK), `age_group_mappings` (M2M to `AgeGroupMapping`), legacy `age_group`/`sge_age_category` (str, deprecated) |
| `ClientBridge` | Maps Arena OAuth client → set of event bridges. | `arena_client` (FK), `eventos_match` (M2M) |
| `AthleteBridge` | Maps Arena person/athlete/fighter → SGE athlete. | `sge_id_atleta` (FK), `arena_custom_id` (FK), `arena_athlete` (M2M), `arena_fighter` (M2M) |
| `FightBridge` | Maps Arena fight → SGE fight. | `arena_fight` (FK), `sge_luta` (FK) |

### Endpoints Summary

| Path | Method | Purpose |
|------|--------|---------|
| `/integration/eventos-arena/` | GET | List event bridges (read-only). |
| `/integration/eventos-sge/` | GET | List SGE eventos (read-only). |
| `/integration/matches/eventos/` | GET/POST/PUT/PATCH/DELETE | Full CRUD for event bridges. |
| `/integration/matches/clients/` | GET/POST/PUT/PATCH/DELETE | Full CRUD for client bridges. |
| `/integration/normalized-ranking/<event_id>/` | GET | Normalized SGE fight data with weight class lookup. |
| `/integration/arena-events/<id>/snapshot/` | GET | Arena event snapshot (rankings + fights, no persistence). |
| `/integration/arena-events/<id>/sync-rankings/` | POST | Sync Arena rankings to SGE API. |

### Services Summary

| Function | Purpose | Side Effects |
|----------|---------|--------------|
| `build_event_snapshot` | Fetch Arena rankings/fights and build enriched payloads. | Arena API calls (GET). |
| `sync_event_rankings_to_sge` | Fetch Arena rankings and POST to SGE ranking API. | Arena API calls (GET), SGE API calls (POST). |
| `process_eventos_sge` | Fetch SGE eventos and normalize audience names. | SGE API calls (GET). |

---

## Domain Context

### Systems

- **Arena:** External OAuth-based competition management platform. Hosts events, athletes, fights, rankings. Sends webhooks on data changes.
- **SGE:** Internal sports governance engine. Maintains evento registry, athlete records, fight results, ranking database.

### Key Concepts

1. **Age-group segmentation:** A single Arena event may span multiple age brackets (U15, U17, Senior). Each age bracket can map to a separate SGE evento, requiring multiple `EventBridge` records for one Arena event.

2. **Age Group Mapping System (NEW):** Normalized mappings between Arena and SGE age group naming variations are stored in `normalization.AgeGroupMapping`. EventBridge uses M2M relationships to these mappings for precise age group filtering during ranking sync. See [AGE_GROUP_MAPPING_GUIDE.md](AGE_GROUP_MAPPING_GUIDE.md) for details.

3. **Normalization:** Arena and SGE use different naming conventions for weight classes, sports, and age groups. The `normalization` app provides mapping functions to translate between them.

4. **Mapping resolution:** Integration services resolve the correct `EventBridge` for a given Arena event + age group combination using the age_group_mappings M2M relationship.

5. **Partial sync:** If an Arena ranking lacks an SGE event mapping (`id_evento=null`), it is skipped during sync (not an error).

---

## Migration Notes

- **Canonical model names:** Bridge models were renamed from `EventosMatch`/`ArenaClientsMatch`/`AtletaMatch`/`LutaMatch` to `EventBridge`/`ClientBridge`/`AthleteBridge`/`FightBridge` in migration `0002_safe_bridge_rename_stage1`.
- **Legacy aliases:** Temporary aliases (`EventosMatch = EventBridge`) exist in `models.py` for backward compatibility. All new code should use canonical names.
- **Age-group fields added:** `EventBridge.age_group` and `EventBridge.sge_age_category` were added in migration `0002` to support multi-age-group event mappings. These are now **deprecated** — use `age_group_mappings` instead.
- **Age group mapping system:** Migration `0003_eventbridge_age_group_mappings_and_more` added the `age_group_mappings` M2M field to `EventBridge`, linking to `normalization.AgeGroupMapping` for flexible age group matching. 22 standard mappings available via `python manage.py populate_age_groups`.
- **Unique constraint:** `unique_together = (('arena_event', 'age_group', 'sge_event', 'sge_age_category'))` ensures one bridge per event + age + SGE event combination (legacy constraint maintained for backward compatibility).
- **Arena client function reuse:** `_build_rankings` now uses `get_weight_categories_by_sport_event_id` from `arena.services.arena_client` instead of calling the Arena API directly, and filters categories using the `age_group_mappings` M2M lookup system.

---

## Admin

No models are registered in Django admin. Bridge management is done exclusively via REST API endpoints (`/integration/matches/eventos/`, `/integration/matches/clients/`).

---

## Testing

> ⚠ **TODO:** Test coverage for integration app is incomplete. See `tests.py` for placeholders.

---

## Known Issues / Ambiguities

1. **`event_binding.get_evento_sge_from_fight`:** This function references `event_match.sge_event.all()` as if `sge_event` is M2M, but in the current `EventBridge` model, `sge_event` is a ForeignKey. This is legacy code and may no longer function correctly.
2. **`NormalizedRankingView`:** Silently skips fights where `IdClassePeso` is not found (no error or warning). Consider returning empty weight_class or logging missing mappings.
3. **Webhook integration boundary:** `apps.arena.webhook` imports `integration.models.EventBridge` directly, creating reverse coupling. Consider refactoring to use a service interface or event bus.
4. **SGE API error handling:** `sync_event_rankings_to_sge` does not raise exceptions on SGE API errors — partial failures are returned in the response. Consider adding a failure threshold or alert mechanism.
5. **OAuth credential validation:** Integration endpoints accept `credential_id` but do not validate existence of `ArenaClient` record before calling Arena API. This may result in unhelpful errors if credential ID is invalid.

---

## Next Steps

1. **Test coverage:** Write DRF tests for snapshot/sync endpoints, CRUD ViewSets, and service functions.
2. **Refactor webhook coupling:** Move EventBridge creation/update logic into an integration service and have webhook handler call it via interface.
3. **Add validation:** Validate `credential_id` in serializers (ensure `ArenaClient.objects.filter(pk=credential_id).exists()`).
4. **Document SGE API response contract:** Work with SGE team to document expected response format for `/resultado-rank-arena` endpoint.
5. **Add logging:** Log all Arena API calls and SGE API POSTs for debugging and audit trail.
