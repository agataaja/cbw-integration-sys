# Integration — Cross-App Dependencies
App: integration  
Last documented: May 20, 2026

## Overview

The integration app acts as the **bridge layer** between Arena and SGE domains. It depends on both `apps.arena` (for external API transport and Arena domain models) and `apps.sge` (for SGE domain models), as well as `apps.normalization` (for mapping/parsing helpers). It does NOT depend on `apps.entities`, `apps.analytics`, or `apps.reports`.

---

## Dependency Graph

```
integration
├── arena (domain models + API transport)
├── sge (domain models)
└── normalization (mapping helpers)
```

**Direction of coupling:**
- `integration` → `arena` (reads Arena models, calls Arena API client)
- `integration` → `sge` (reads/writes SGE models via ForeignKey)
- `integration` → `normalization` (calls parsing/mapping functions)
- `arena.webhook` → `integration` (webhook ingress creates/updates EventBridge)

---

## Dependencies on `apps.arena`

### Models

| Model | Relationship | Field | Purpose |
|-------|--------------|-------|---------|
| `ArenaSportEvent` | ForeignKey | `EventBridge.arena_event` | Links event bridge to Arena event. |
| `ArenaClient` | ForeignKey | `ClientBridge.arena_client` | Links client bridge to OAuth credential. |
| `ArenaPerson` | ForeignKey (Nullable) | `AthleteBridge.arena_custom_id` | Links athlete bridge to Arena person entity. |
| `ArenaAthlete` | ManyToManyField | `AthleteBridge.arena_athlete` | Links athlete bridge to Arena athlete entities. |
| `ArenaFighter` | ManyToManyField | `AthleteBridge.arena_fighter` | Links athlete bridge to Arena fighter entities (competition-specific). |
| `ArenaFight` | ForeignKey (Nullable) | `FightBridge.arena_fight` | Links fight bridge to Arena fight record. |

**Import locations:**
- `integration/models.py` → `from apps.arena.models import ArenaPerson, ArenaAthlete, ArenaFighter, ArenaSportEvent, ArenaFight, ArenaClient`

**Business reason:**  
Integration models represent mappings between Arena entities and SGE entities. These FKs store the "Arena side" of each bridge.

---

### Services

| Service Function | Import Path | Purpose |
|------------------|-------------|---------|
| `get_headers` | `apps.arena.services.arena_client` | Fetches OAuth headers for Arena API calls. |
| `get_endpoint_response` | `apps.arena.services.arena_client` | Generic Arena API GET wrapper (handles OAuth, retries, JSON parsing). |
| `get_weight_categories_by_sport_event_id` | `apps.arena.services.arena_client` | Fetches all weight categories for an Arena event, returns dict of {category_id: shortName}. |
| `get_all_fights_by_event_id` | `apps.arena.services.arena_client` | Fetches all fights for a given Arena event. |
| `get_all_sge_eventos_info` | `apps.arena.integrations.sge_rest_api` | Fetches SGE eventos from SGE REST API (transitional location, may belong in SGE domain). |

**Import locations:**
- `integration/services/arena_sge.py` → `from apps.arena.services.arena_client import get_all_fights_by_event_id, get_endpoint_response, get_headers`
- `integration/services/sge_events.py` → `from apps.arena.integrations.sge_rest_api import get_all_sge_eventos_info`

**Business reason:**  
Integration services orchestrate Arena data fetching and SGE sync. Arena API transport logic is encapsulated in `apps.arena.services.arena_client`, maintaining domain separation.

---

## Dependencies on `apps.sge`

### Models

| Model | Relationship | Field | Purpose |
|-------|--------------|-------|---------|
| `GestaoEventos` | ForeignKey | `EventBridge.sge_event` | Links event bridge to SGE evento. |
| `GestaoAtletas` | ForeignKey | `AthleteBridge.sge_id_atleta` | Links athlete bridge to SGE athlete record. |
| `GestaoIdsAtletas` | ForeignKey | `AthleteBridge.sge_id` | Links athlete bridge to SGE athlete IDs record. |
| `LutaSGE` | ForeignKey | `FightBridge.sge_luta` | Links fight bridge to SGE fight record. |

**Import locations:**
- `integration/models.py` → `from apps.sge.models import GestaoEventos, GestaoAtletas, GestaoIdsAtletas, LutaSGE`
- `integration/serializers.py` → `from apps.sge.models import GestaoEventos`
- `integration/views.py` → `from apps.sge.models import GestaoEventos, LutaSGE`

**Business reason:**  
Integration models represent mappings between Arena entities and SGE entities. These FKs store the "SGE side" of each bridge.

---

## Dependencies on `apps.normalization`

### Models

| Model | Used In | Purpose |
|-------|---------|---------|
| `AgeGroupMapping` | `models.py`, `serializers.py`, `services/arena_sge.py` | Normalized mappings between Arena and SGE age group naming variations. EventBridge uses M2M relationship to link age groups. |
| `IdClassePeso` | `views.py`, `services/arena_sge.py` | Looks up SGE weight class ID by (estilo, categoria, ano, escopo). |

**Import locations:**
- `integration/models.py` → `from apps.normalization.models import AgeGroupMapping`
- `integration/serializers.py` → `from apps.normalization.models import AgeGroupMapping`
- `integration/services/arena_sge.py` → `from apps.normalization.models import AgeGroupMapping`
- `integration/views.py` → `from apps.normalization.models import IdClassePeso`
- `integration/services/arena_sge.py` → `from apps.normalization.models import IdClassePeso`

---

### Services

| Service Function | Import Path | Purpose |
|------------------|-------------|---------|
| `parse_weight_category` | `apps.normalization.services.mapping` | Parses Arena weight category name (e.g., "61kg U17 Freestyle") into `{sport_name, weight_name, audience_name}`. |
| `infer_sport_alternate_name` | `apps.normalization.services.mapping` | Maps sport name to SGE sport code (e.g., "Wrestling Freestyle" → "LL"). |
| `normalize_audience_name` | `apps.normalization.services.mapping` | Normalizes Arena age group name to SGE format (e.g., "U17" → "SUB 17"). |
| `map_audience_name_by_name` | `apps.normalization.services.mapping` | Infers audience name from event description. |

**Import locations:**
- `integration/services/arena_sge.py` → `from apps.normalization.services.mapping import infer_sport_alternate_name, normalize_audience_name, parse_weight_category`
- `integration/services/sge_events.py` → `from apps.normalization.services.mapping import map_audience_name_by_name`

**Business reason:**  
Arena and SGE use different naming conventions for weight classes, sports, and age groups. Normalization services provide pure mapping functions to translate between the two systems.

---

## Reverse Dependencies (Apps that depend on `integration`)

### `apps.arena.webhook`

The Arena webhook ingress module (`apps.arena.webhook.*`) creates or updates `EventBridge` and `ClientBridge` records when Arena webhooks are received.

**Import location:** `apps.arena.services.webhook_ingress` or `apps.arena.webhook.*`

**Coupling direction:** `arena.webhook` → `integration`

**Business reason:**  
When Arena sends a webhook notification (e.g., event created, results updated), the webhook handler checks if an `EventBridge` exists and routes the data into SGE sync logic.

> ⚠ **Note:** This is an architectural boundary crossing. Ideally, webhook ingress should remain in the Arena domain, and integration orchestration should be triggered via service calls (not direct model imports). Consider refactoring to use a service interface or event bus.

---

## Environment-Driven Dependencies

### SGE API Endpoints

Integration services POST data to external SGE REST API:

| Endpoint | Environment Variable | Default Value |
|----------|---------------------|---------------|
| Ranking sync | `SGE_ARENA_API_URL` | `https://restcbw.bigmidia.com/cbw/api` |
| Final URL | — | `{SGE_ARENA_API_URL}/resultado-rank-arena` |

**Usage:** `integration/services/arena_sge.py` → `sync_event_rankings_to_sge`

**Business reason:**  
Rankings fetched from Arena must be POSTed to SGE to update the SGE ranking database. This is an external HTTP dependency, not a Django app dependency.

---

## Summary Table

| App | Models Used | Services Used | Direction | Reason |
|-----|-------------|---------------|-----------|--------|
| `arena` | `ArenaSportEvent`, `ArenaClient`, `ArenaPerson`, `ArenaAthlete`, `ArenaFighter`, `ArenaFight` | `get_headers`, `get_endpoint_response`, `get_all_fights_by_event_id` | `integration` → `arena` | Bridge models link to Arena entities; services fetch Arena data. |
| `sge` | `GestaoEventos`, `GestaoAtletas`, `GestaoIdsAtletas`, `LutaSGE` | None | `integration` → `sge` | Bridge models link to SGE entities. |
| `normalization` | `IdClassePeso` | `parse_weight_category`, `infer_sport_alternate_name`, `normalize_audience_name`, `map_audience_name_by_name` | `integration` → `normalization` | Weight class/age group/sport mapping. |
| `arena.webhook` | `EventBridge`, `ClientBridge` | None | `arena.webhook` → `integration` | Webhook ingress updates bridge models. |

---

## Notes

- **No circular dependencies:** Integration depends on arena, sge, and normalization. Arena's webhook layer depends back on integration, but this is a one-way coupling from webhook ingress (not core Arena models).
- **External API dependency:** Integration services call Arena API (via `arena.services.arena_client`) and SGE REST API (direct HTTP POST).
- **Domain separation:** Integration does NOT import from `entities`, `analytics`, or `reports` — it is a pure bridge layer between Arena and SGE.
