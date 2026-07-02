# Integration — Serializers
App: integration  
Last documented: May 20, 2026

## Overview

Integration app serializers define request/response shapes for event bridge CRUD, client bridge CRUD, and Arena-to-SGE orchestration endpoints (snapshot, sync). Read-only serializers include nested representations; write serializers use primary keys for relationships.

---

## Serializers

### AgeGroupMappingSerializer

**Type:** Read-only  
**Model:** `normalization.AgeGroupMapping`  
**Purpose:** Represents normalized age group mapping data in nested responses.

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Age group mapping primary key. |
| `canonical_name` | String | Normalized age group name based on Arena identifier (e.g., "u17", "seniors"). |
| `arena_variations` | Array[String] | List of Arena age group name variations (e.g., ["U17", "u17", "Sub-17", "Under 17"]). |
| `sge_variations` | Array[String] | List of SGE age category variations (e.g., ["Sub-17", "SUB 17", "U17"]). First is primary. |
| `sort_order` | Integer | Display order (youngest to oldest). |

**Usage:** Nested in `EventosArenaSerializer` to show linked age group mappings.

---

### EventosSgeSerializer

**Type:** Read-only  
**Model:** `sge.GestaoEventos`  
**Purpose:** Represents SGE event data in nested responses.

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | SGE event primary key. |
| `descricao` | String | Event description. |
| `escopo` | String | Event scope (e.g., "Nacional", "Internacional"). |
| `data_inicio` | Date | Event start date. |
| `data_fim` | Date | Event end date. |

**Usage:** Nested in `EventosArenaSerializer` to show linked SGE event details.

---

### EventosArenaSerializer

**Type:** Read-only  
**Model:** `integration.EventBridge`  
**Purpose:** Displays event bridge with nested SGE event.

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Bridge primary key. |
| `nome` | String | Bridge name/label. |
| `age_group` | String (Nullable) | **DEPRECATED.** Legacy Arena age group. |
| `sge_age_category` | String (Nullable) | **DEPRECATED.** Legacy SGE age category. |
| `age_group_mappings` | Array[Object] | Nested `AgeGroupMappingSerializer` representations (read-only). |
| `arena_event` | Integer | Arena event FK (ID only). |
| `sge_event` | Object | Nested `EventosSgeSerializer` representation. |
| `created_at` | DateTime | Bridge creation timestamp. |

**Example Response:**
```json
{
  "id": 42,
  "nome": "World Championship U17",
  "age_group": null,
  "sge_age_category": null,
  "age_group_mappings": [
    {
      "id": 9,
      "canonical_name": "u17",
      "arena_variations": ["u17", "U17", "U-17", "Sub-17", "SUB 17", "Under 17", "Cadete"],
      "sge_variations": ["Sub-17", "SUB 17", "U17", "U-17"],
      "sort_order": 70
    }
  ],
  "arena_event": 101,
  "sge_event": {
    "id": 5,
    "descricao": "Mundial Sub 17",
    "escopo": "Internacional",
    "data_inicio": "2026-06-01",
    "data_fim": "2026-06-05"
  },
  "created_at": "2026-05-19T12:34:56Z"
}
```

---

### EventosBridgeSerializer

**Type:** Read/write  
**Model:** `integration.EventBridge`  
**Purpose:** Create or update event bridges.

| Field | Type | Required | Writable | Description |
|-------|------|----------|----------|-------------|
| `id` | Integer | No | No | Bridge ID (read-only, auto-generated). |
| `nome` | String | Yes | Yes | Bridge name. |
| `age_group` | String | No | Yes | **DEPRECATED.** Legacy Arena age group identifier. |
| `sge_age_category` | String | No | Yes | **DEPRECATED.** Legacy SGE age category. |
| `age_group_mapping_ids` | Array[Integer] | No | Yes (write-only) | List of AgeGroupMapping IDs to associate (uses M2M relationship). |
| `arena_event` | Integer | Yes | Yes | Arena event FK (ID). |
| `sge_event` | Integer | Yes | Yes | SGE event FK (ID). |
| `created_at` | DateTime | No | No | Read-only timestamp. |

**Example Request (New System):**
```json
{
  "nome": "World Championship U17",
  "arena_event": 101,
  "sge_event": 5,
  "age_group_mapping_ids": [9]
}
```

**Example Request (Legacy System - Deprecated):**
```json
{
  "nome": "World Championship U17",
  "age_group": "U17",
  "sge_age_category": "SUB 17",
  "arena_event": 101,
  "sge_event": 5
}
```

**Logic:**
- On `create` or `update`: if `age_group_mapping_ids` provided, sets M2M `age_group_mappings` via `instance.age_group_mappings.set(...)`.

**Validation:**
- Legacy `unique_together` constraint still enforced at DB level for backward compatibility.

---

### ArenaClientsMatchSerializer

**Type:** Read-only  
**Model:** `integration.ClientBridge`  
**Purpose:** Displays client bridge with nested event bridges.

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Client bridge primary key. |
| `arena_client` | Integer | Arena client FK (ID only). |
| `eventos_match` | Array[Object] | Nested `EventosArenaSerializer` representations. |
| `created_at` | DateTime | Bridge creation timestamp. |

**Example Response:**
```json
{
  "id": 10,
  "arena_client": 3,
  "eventos_match": [
    {
      "id": 42,
      "nome": "World Championship U17",
      "age_group": "U17",
      "sge_age_category": "SUB 17",
      "arena_event": 101,
      "sge_event": {...},
      "created_at": "2026-05-19T12:34:56Z"
    }
  ],
  "created_at": "2026-05-10T08:00:00Z"
}
```

---

### ArenaClientsMatchWriteSerializer

**Type:** Read/write  
**Model:** `integration.ClientBridge`  
**Purpose:** Create or update client bridges with M2M event assignments.

| Field | Type | Required | Writable | Description |
|-------|------|----------|----------|-------------|
| `id` | Integer | No | No | Read-only. |
| `arena_client` | Integer | Yes | Yes | Arena client FK (ID). |
| `eventos_match_ids` | Array[Integer] | No | Yes (write-only) | List of EventBridge IDs to associate. |
| `created_at` | DateTime | No | No | Read-only timestamp. |

**Example Request (Create):**
```json
{
  "arena_client": 3,
  "eventos_match_ids": [42, 43]
}
```

**Example Request (Update):**
```json
{
  "arena_client": 3,
  "eventos_match_ids": [42, 44]
}
```

**Logic:**
- On `create`: sets M2M `eventos_match` via `validated_data.pop('eventos_match')` and `instance.eventos_match.set(...)`.
- On `update`: replaces M2M relationships if `eventos_match_ids` is provided (or leaves unchanged if omitted).

---

### ArenaEventSnapshotRequestSerializer

**Type:** Request-only (Serializer, not ModelSerializer)  
**Purpose:** Validates query parameters for `/arena-events/<id>/snapshot/` endpoint.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `credential_id` | Integer | Yes | Arena OAuth credential ID (must be ≥ 1). |
| `sge_event_id` | Integer | No | Explicit SGE event ID to use for mapping (overrides auto-resolution). |

**Usage:**  
Client sends:
```
GET /integration/arena-events/abc123/snapshot/?credential_id=2&sge_event_id=5
```

---

### ArenaEventSyncRequestSerializer

**Type:** Request-only (Serializer, not ModelSerializer)  
**Purpose:** Validates POST body for `/arena-events/<id>/sync-rankings/` endpoint.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `credential_id` | Integer | Yes | Arena OAuth credential ID (must be ≥ 1). |
| `sge_event_id` | Integer | No | Explicit SGE event ID for ranking sync (overrides auto-resolution). |

**Example Request:**
```json
{
  "credential_id": 2,
  "sge_event_id": 5
}
```

---

## Notes

- **Read vs Write split:** List/retrieve actions use read serializers (nested, denormalized); create/update/delete use write serializers (flat, ID-based).
- **M2M handling:** `ArenaClientsMatchWriteSerializer` uses `write_only` PK field for M2M assignment and manually manages the relationship in `create`/`update`.
- **Request-only serializers:** Snapshot/sync request serializers validate input but don't persist data — service layer orchestrates the business logic.
