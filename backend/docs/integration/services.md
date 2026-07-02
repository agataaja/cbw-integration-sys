# Integration — Services
App: integration  
Last documented: May 20, 2026

## Overview

Integration services orchestrate cross-domain logic: fetching Arena data via OAuth, mapping age groups and weight categories, resolving EventBridge mappings, building ranking payloads, and syncing data to SGE REST API. These services do NOT persist data to integration models — they read bridges and write to external systems or return ephemeral snapshots.

---

## Module: `services.arena_sge`

**Purpose:** Core Arena-to-SGE orchestration: snapshot generation, ranking sync, and payload construction.

---

### Function: `build_event_snapshot`

**Signature:**
```python
def build_event_snapshot(
    credentials_pk: int, 
    arena_event_id: str, 
    sge_event_id: int | None = None
) -> dict[str, Any]
```

**Purpose:** Generates a complete snapshot of an Arena event's rankings and fights without persisting to SGE.

**Arguments:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `credentials_pk` | `int` | Yes | Arena OAuth client credential ID. |
| `arena_event_id` | `str` | Yes | Arena event UUID or identifier. |
| `sge_event_id` | `int | None` | No | Explicit SGE event ID (overrides auto-mapping resolution). |

**Returns:**
```python
{
    "arena_event_id": str,
    "rankings": list[dict],    # List of ranking payloads (one per fighter per weight category)
    "fights": list[dict],       # List of fight payloads
    "unresolved_rankings": list[dict]  # Rankings with no SGE event mapping
}
```

**Flow:**
1. Calls `_build_rankings(credentials_pk, arena_event_id, explicit_sge_event_id=sge_event_id)`.
2. Calls `_build_fights(credentials_pk, arena_event_id)`.
3. Filters rankings where `id_evento` is null → `unresolved_rankings`.
4. Returns combined snapshot.

**Raises:** `ArenaIntegrationError` if event is not in the `EventBridge` table.

**Side effects:** Fetches data from Arena API via `apps.arena.services.arena_client`.

---

### Function: `sync_event_rankings_to_sge`

**Signature:**
```python
def sync_event_rankings_to_sge(
    credentials_pk: int, 
    arena_event_id: str, 
    sge_event_id: int | None = None
) -> dict[str, Any]
```

**Purpose:** Fetches Arena rankings and POSTs each payload to SGE ranking API (`/cbw/api/resultado-rank-arena`).

**Arguments:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `credentials_pk` | `int` | Yes | Arena OAuth client credential ID. |
| `arena_event_id` | `str` | Yes | Arena event UUID or identifier. |
| `sge_event_id` | `int | None` | No | Explicit SGE event ID (overrides auto-mapping resolution). |

**Returns:**
```python
{
    "arena_event_id": str,
    "sent": int,           # Number of payloads successfully POSTed
    "skipped": int,        # Number of payloads skipped (no mapping)
    "responses": list[dict],  # HTTP responses for each POST
    "skipped_items": list[dict]  # Skipped payloads with reasons
}
```

**Flow:**
1. Calls `_build_rankings(credentials_pk, arena_event_id, explicit_sge_event_id=sge_event_id)`.
2. For each ranking payload:
   - If `payload["id_evento"]` is null → skip (add to `skipped_items` with reason `"missing_sge_event_mapping"`).
   - Else → POST to `SGE_RANKING_API_URL` with JSON payload.
3. Returns summary of sent/skipped items with HTTP status codes and response text.

**Environment Variables:**
- `SGE_ARENA_API_URL` (default: `https://restcbw.bigmidia.com/cbw/api`)
- Final URL: `{SGE_ARENA_API_URL}/resultado-rank-arena`

**HTTP Contract (SGE Ranking API):**
- **Method:** POST
- **Content-Type:** `application/json`
- **Timeout:** 30 seconds
- **Payload schema:** See `_build_rankings` payload structure below.

**Raises:** `ArenaIntegrationError` if event is not in the `EventBridge` table.

**Side effects:** Writes to external SGE ranking API.

---

### Internal Function: `_build_rankings`

**Signature:**
```python
def _build_rankings(
    credentials_pk: int, 
    arena_event_id: str, 
    explicit_sge_event_id: int | None = None
) -> list[dict[str, Any]]
```

**Purpose:** Constructs ranking payloads for all fighters in all weight categories of an Arena event, enriched with SGE mapping and normalization.

**Flow:**
1. Fetch Arena weight categories via `arena.services.arena_client.get_weight_categories_by_sport_event_id(arena_event_id, pk=credentials_pk)` → returns dict of `{category_id: shortName}`.
2. Query `EventBridge` records for the arena_event_id with prefetched `age_group_mappings` (M2M relationship to `normalization.AgeGroupMapping`).
3. Build an `age_group_lookup` dictionary mapping all Arena age group variations → `(EventBridge, primary_sge_variation, age_mapping)`:
   - For each EventBridge:
     - For each linked AgeGroupMapping:
       - For each arena_variation in mapping.arena_variations:
         - `age_group_lookup[arena_variation.upper()] = (bridge, mapping.primary_sge_variation, mapping)`
   - Fallback: If bridge has legacy `age_group` string and no mappings, add legacy lookup.
4. For each weight category:
   - Parse category name via `normalization.parse_weight_category` to extract `{sport_name, weight_name, audience_name}`.
   - Lookup matching bridge using `age_group_lookup.get(audience_name.upper())`.
   - If no match found, skip category (continue to next).
   - Fetch ranking data via `get_endpoint_response(headers, f"weight-category/get/{category_id}/ranking")`.
   - Extract `ranking` (dict or list) and iterate over ranking items.
5. For each ranking item (fighter):
   - Resolve `id_evento` via `_resolve_sge_event_id(bridge, explicit_sge_event_id)`.
   - Resolve `id_classe_peso` via `_resolve_id_classe_peso(matching_sge_event, parsed_category)`.
   - Fetch fighter's `customId` from Arena via `_get_person_custom_id(headers, credentials_pk, person_id, cache)`.
   - Build payload dict using matched `primary_sge_variation` as `audienceName`.
6. Return list of payloads.

**Payload Structure (per fighter):**
```python
{
    "id_evento": int | None,              # SGE event ID (null if no mapping)
    "id_evento_arena": str,               # Arena event ID
    "countFighters": str,                 # Total fighters in weight category
    "countFights": str,                   # Total fights in weight category
    "weightCategoryFullName": str,        # Original Arena category name
    "customId": str,                      # Arena person customId (empty if not found)
    "fullName": str,                      # Fighter full name
    "rank": str,                          # Rank position
    "sportAlternateName": str,            # Normalized sport code (e.g., "LL", "LG")
    "sportName": str,                     # Parsed sport name
    "name": str,                          # Parsed weight class name
    "audienceName": str,                  # Primary SGE variation from matched AgeGroupMapping
    "id_classe_peso": int | None,         # SGE weight class ID (null if not found)
    "source_category_id": str,            # Arena category ID
    "match_id": int | None,               # EventBridge ID (null if no mapping)
    "age_group_mapping_id": int | None    # AgeGroupMapping ID used for this category (null if legacy/no mapping)
}
```

**Dependencies:**
- `apps.arena.services.arena_client.get_weight_categories_by_sport_event_id`
- `apps.arena.services.arena_client.get_endpoint_response`
- `apps.normalization.models.AgeGroupMapping` (via EventBridge.age_group_mappings M2M)
- `apps.normalization.services.mapping.parse_weight_category`
- `apps.normalization.services.mapping.infer_sport_alternate_name`
- `_resolve_event_binding`
- `_resolve_sge_event_id`
- `_resolve_id_classe_peso`
- `_get_person_custom_id`

**Note:** The `normalize_audience_name` and `_resolve_mapping_for_age_group` functions are no longer used. Age group resolution is now handled via the `age_group_lookup` dictionary built from `EventBridge.age_group_mappings`.

---

### Internal Function: `_build_fights`

**Signature:**
```python
def _build_fights(
    credentials_pk: int, 
    arena_event_id: str
) -> list[dict[str, Any]]
```

**Purpose:** Fetches all fights for an Arena event and constructs enriched fight payloads.

**Flow:**
1. Fetch all fights via `arena.services.arena_client.get_all_fights_by_event_id(arena_event_id, pk=credentials_pk)`.
2. For each fight:
   - Fetch `customId` for `fighter1PersonId` and `fighter2PersonId` via `_get_person_custom_id` (cached).
   - Build fight payload dict.
3. Return list of fight payloads.

**Payload Structure (per fight):**
```python
{
    "fight_id": str,
    "fight_number": str,
    "winner_fighter_id": str,
    "result": str,
    "victory_type": str,
    "ranking_point_nice_name": str,
    "weight_category_id": str,
    "weight_category_name": str,
    "fighter1_name": str,
    "fighter1_custom_id": str,
    "fighter2_name": str,
    "fighter2_custom_id": str,
    "team1": str,
    "team2": str,
    "end_time": str
}
```

---

### Internal Function: `_resolve_event_binding`

**Signature:**
```python
def _resolve_event_binding(arena_event_id: str) -> EventBridge
```

**Purpose:** Fetches the first `EventBridge` for a given Arena event ID. Validates that the event is registered in the integration table.

**Raises:** `ArenaIntegrationError` if no `EventBridge` exists for `arena_event__event_id=arena_event_id`.

**Note:** This function does NOT handle age-group-specific mappings — it only checks for existence. For age-group resolution, use `_resolve_mapping_for_age_group`.

---

### Internal Function: `_resolve_mapping_for_age_group`

**Signature:**
```python
def _resolve_mapping_for_age_group(
    arena_event_id: str, 
    age_group: str
) -> EventBridge | None
```

**Purpose:** Resolves the correct `EventBridge` for an Arena event + age group combination.

**Logic:**
1. Filter `EventBridge` by `arena_event__event_id=arena_event_id`.
2. If `age_group` is provided:
   - Subfilter by `age_group__iexact=age_group`.
   - If match found, return first.
3. If no age-specific match, return first match (fallback for single-mapping events).
4. If no match at all, return `None`.

**Domain Context:** A single Arena event may have multiple `EventBridge` records (one per age group). This function selects the correct mapping based on parsed age group from weight category name.

---

### Internal Function: `_resolve_sge_event_id`

**Signature:**
```python
def _resolve_sge_event_id(
    event_match: EventBridge | None, 
    explicit_sge_event_id: int | None
) -> int | None
```

**Purpose:** Determines the SGE event ID to use for a ranking payload.

**Logic:**
1. If `explicit_sge_event_id` is provided, return it (override).
2. Else if `event_match` and `event_match.sge_event_id` exist, return `event_match.sge_event_id`.
3. Else return `None` (no mapping → ranking will be skipped in sync).

---

### Internal Function: `_resolve_id_classe_peso`

**Signature:**
```python
def _resolve_id_classe_peso(
    evento_sge: GestaoEventos | None, 
    parsed_category: dict[str, str]
) -> int | None
```

**Purpose:** Looks up the SGE weight class ID (`id_classe_peso`) from `normalization.IdClassePeso` using parsed category fields and event context.

**Filters:**
```python
{
    "estilo__iexact": parsed_category["sport_alternate_name"],
    "categoria__iexact": parsed_category["weight_name"],
    "ano": str(evento_sge.data_fim)[:4],  # If evento_sge and data_fim exist
    "escopo__iexact": evento_sge.escopo,  # If evento_sge.escopo exists
    # OR
    "escopo__iexact": parsed_category["audience_name"]  # If no evento_sge.escopo
}
```

**Returns:** First matching `id_classe_peso` or `None`.

**Domain Context:** SGE weight classes are stored in `IdClassePeso` with year, scope, sport, and category. This function performs a fuzzy lookup using case-insensitive matching.

---

### Internal Function: `_get_person_custom_id`

**Signature:**
```python
def _get_person_custom_id(
    headers: dict[str, str], 
    credentials_pk: int, 
    person_id: Any, 
    cache: dict[str, str]
) -> str
```

**Purpose:** Fetches a person's `customId` from Arena API and caches it to avoid duplicate HTTP calls.

**Flow:**
1. Check cache (`cache[str(person_id)]`).
2. If not cached, call `get_endpoint_response(headers, f"person/get/{person_id}", pk=credentials_pk)`.
3. Extract `response.get("person", {}).get("customId") or ""`.
4. Store in cache and return.

**Cache:** Passed as mutable dict (`person_cache`) across all ranking items to minimize API calls.

---

### Internal Function: `_iter_ranking_items`

**Signature:**
```python
def _iter_ranking_items(ranking_payload: Any) -> list[dict[str, Any]]
```

**Purpose:** Normalizes Arena ranking response (which can be dict or list) into a list of ranking items.

**Logic:**
- If `ranking_payload` is `dict` → return `list(ranking_payload.values())`.
- If `ranking_payload` is `list` → return as-is.
- Else → return `[]`.

**Domain Context:** Arena API inconsistently returns rankings as either `{"1": {...}, "2": {...}}` or `[{...}, {...}]`.

---

## Module: `services.event_binding`

**Purpose:** Legacy module for resolving SGE event ID from fight data.

---

### Function: `get_evento_sge_from_fight`

**Signature:**
```python
def get_evento_sge_from_fight(
    fight_data, 
    sport_event_id=None
) -> int | None
```

**Purpose:** Resolves SGE event ID from fight data dict, using `EventBridge` mapping.

**Arguments:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `fight_data` | `dict` | Yes | Fight data dict (must contain `sportEventId` or `audienceName`). |
| `sport_event_id` | `Any` | No | Explicit Arena sport event ID (overrides `fight_data.get('sportEventId')`). |

**Returns:** SGE event ID (`int`) or `None` if no mapping found.

**Flow:**
1. Resolve `sport_event_id` (from param or `fight_data.get('sportEventId')`).
2. Fetch `EventBridge` by `arena_event__event_id=sport_event_id`.
3. Get all linked `GestaoEventos` via `event_match.sge_event.all()` (M2M).
4. If `fight_data.get('audienceName')` exists, filter eventos by `audienceName__iexact`.
5. If match found, return `evento_sge.id`.
6. If only one evento exists, return its ID.
7. Else return `None`.

> ⚠ **Ambiguous:** This function references `event_match.sge_event.all()` as if `sge_event` is M2M, but in current `EventBridge` model, `sge_event` is a ForeignKey. This is legacy code from before the bridge model rename and may no longer function correctly.

---

## Module: `services.sge_events`

**Purpose:** Fetches and normalizes SGE event data without persisting integration models.

---

### Function: `process_eventos_sge`

**Signature:**
```python
def process_eventos_sge() -> list[dict]
```

**Purpose:** Fetches all SGE eventos from the SGE REST API and enriches with normalized audience names.

**Returns:**
```python
[
    {
        "id": int,
        "descricao": str,
        "escopo": str,
        "data_inicio": date,
        "data_fim": date,
        "audience_name": str,  # Normalized via normalization.map_audience_name_by_name
        "ano": str
    }
]
```

**Flow:**
1. Call `arena.integrations.sge_rest_api.get_all_sge_eventos_info()` → pandas DataFrame.
2. For each row, extract fields and normalize `descricao` → `audience_name`.
3. Return list of dicts.

**Side effects:** Fetches data from SGE REST API.

**Dependencies:**
- `arena.integrations.sge_rest_api.get_all_sge_eventos_info`
- `normalization.services.mapping.map_audience_name_by_name`

---

## Exception: `ArenaIntegrationError`

**Purpose:** Custom exception raised by integration services when Arena-SGE orchestration fails (e.g., event not registered in bridge table, invalid credentials).

**Usage:**
```python
raise ArenaIntegrationError("Arena event abc123 is not registered in integration match table.")
```

---

## Notes

- **No persistence:** Integration services read from Arena/SGE and EventBridge, but do NOT create/update bridge models — that is done manually via CRUD endpoints.
- **Caching:** `_get_person_custom_id` uses an in-memory cache dict to avoid duplicate Arena API calls within a single request.
- **External API calls:** All Arena API calls go through `apps.arena.services.arena_client` (OAuth-aware transport layer). SGE ranking sync POSTs directly to `SGE_RANKING_API_URL`.
- **Normalization:** Weight category parsing and audience name normalization are delegated to `apps.normalization.services.mapping`.
