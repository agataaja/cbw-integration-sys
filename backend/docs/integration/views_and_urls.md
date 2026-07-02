# Integration — Views and URLs
App: integration  
Last documented: May 20, 2026

## Overview

Integration app exposes:
1. **Read-only ViewSets** for browsing event bridges (with nested age group mappings) and SGE eventos.
2. **Full CRUD ViewSets** for manual event/client bridge management (supports age group mapping assignment).
3. **Orchestration APIViews** for Arena snapshot and ranking sync (uses age group mappings for category filtering).
4. **Legacy normalized ranking view** (SGE fight data normalization).

All endpoints are mounted under `/integration/`.

> **Age Group Mapping System:** EventBridge records now use M2M relationships to `normalization.AgeGroupMapping` for flexible age group matching across Arena and SGE naming variations. See [AGE_GROUP_MAPPING_GUIDE.md](AGE_GROUP_MAPPING_GUIDE.md) for details.

---

## ViewSets

### EventosArenaViewSet

**Type:** `viewsets.ReadOnlyModelViewSet`  
**Queryset:** `EventBridge.objects.select_related('arena_event', 'sge_event').all()`  
**Serializer:** `EventosArenaSerializer` (includes nested `age_group_mappings`)  
**Basename:** `eventos-arena`  

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/integration/eventos-arena/` | List all event bridges (with nested SGE event data and age group mappings). |
| GET | `/integration/eventos-arena/<id>/` | Retrieve a single event bridge. |

**Permissions:** None specified (default: allow all).  
**Pagination:** DRF default.

> **Note:** Response includes `age_group_mappings` array with full `AgeGroupMapping` details (canonical_name, arena_variations, sge_variations, sort_order).

---

### EventosBridgeViewSet

**Type:** `viewsets.ModelViewSet`  
**Queryset:** `EventBridge.objects.select_related('arena_event', 'sge_event').all().order_by('-id')`  
**Serializers:** Dynamic based on action:
- List/Retrieve → `EventosArenaSerializer` (includes nested `age_group_mappings`)
- Create/Update/Delete → `EventosBridgeSerializer` (supports `age_group_mapping_ids`)

**Basename:** `eventos-match`

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/integration/bridge/eventos/` | List event bridges (newest first). |
| POST | `/integration/bridge/eventos/` | Create a new event bridge. |
| GET | `/integration/bridge/eventos/<id>/` | Retrieve a single event bridge. |
| PUT | `/integration/bridge/eventos/<id>/` | Update an event bridge (full). |
| PATCH | `/integration/bridge/eventos/<id>/` | Update an event bridge (partial). |
| DELETE | `/integration/bridge/eventos/<id>/` | Delete an event bridge. |

**Request Example (POST - New System):**
```json
{
  "nome": "Mundial U17",
  "arena_event": 101,
  "sge_event": 5,
  "age_group_mapping_ids": [9]
}
```

**Request Example (POST - Legacy System, Deprecated):**
```json
{
  "nome": "Mundial U17",
  "age_group": "U17",
  "sge_age_category": "SUB 17",
  "arena_event": 101,
  "sge_event": 5
}
```

**Response Example (GET list, single item):**
```json
{
  "id": 42,
  "nome": "Mundial U17",
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

> **Note:** Legacy `age_group` and `sge_age_category` fields are deprecated. New implementations should use `age_group_mapping_ids` (write) and `age_group_mappings` (read). See [AGE_GROUP_MAPPING_GUIDE.md](AGE_GROUP_MAPPING_GUIDE.md) for details.

**Custom Actions:**

#### GET `snapshot` - Get Arena Event Snapshot

**Path:** `/integration/bridge/eventos/<id>/snapshot/`

**Purpose:** Builds a complete Arena event data snapshot (rankings + fights) for this specific EventBridge without persisting to SGE. Uses the bridge's arena_event, sge_event, and age_group_mappings directly.

**Query Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `credential_id` | Integer | Yes | Arena OAuth client credential ID. |

**Request Example:**
```
GET /integration/bridge/eventos/42/snapshot/?credential_id=2
```

**Response Example:**
```json
{
  "event_bridge_id": 42,
  "arena_event_id": "abc123",
  "sge_event_id": 5,
  "rankings": [
    {
      "id_evento": 5,
      "id_evento_arena": "abc123",
      "customId": "12345",
      "fullName": "John Doe",
      "rank": "1",
      "sportName": "Wrestling",
      "sportAlternateName": "LL",
      "name": "61kg",
      "audienceName": "Sub-17",
      "id_classe_peso": 42,
      "source_category_id": "cat-101",
      "match_id": 42,
      "age_group_mapping_id": 9
    }
  ],
  "fights": [
    {
      "fight_id": "fight-xyz",
      "fight_number": "1",
      "winner_fighter_id": "fighter-1",
      "result": "VPO",
      "victory_type": "Points",
      "ranking_point_nice_name": "3",
      "weight_category_id": "cat-101",
      "weight_category_name": "61kg U17 Freestyle",
      "fighter1_name": "John Doe",
      "fighter1_custom_id": "12345",
      "fighter2_name": "Jane Smith",
      "fighter2_custom_id": "67890",
      "team1": "Team A",
      "team2": "Team B",
      "end_time": "2026-05-19T15:30:00Z"
    }
  ],
  "unresolved_rankings": []
}
```

**Logic:**
1. Fetches the EventBridge with its arena_event, sge_event, and age_group_mappings.
2. Uses arena_event.event_id to query Arena API for weight categories and rankings.
3. Filters categories based on the bridge's age_group_mappings (only matching age groups).
4. Uses sge_event.id for all ranking payloads.
5. Returns snapshot with rankings and fights.

**Errors:**
- `400 Bad Request` if EventBridge not found or has no arena_event.
- `400 Bad Request` if `credential_id` is invalid or `ArenaIntegrationError` is raised.

#### POST `sync_rankings` - Sync Rankings to SGE

**Path:** `/integration/bridge/eventos/<id>/sync-rankings/`

**Purpose:** Fetches Arena rankings for this EventBridge and POSTs them to the SGE ranking API (`/cbw/api/resultado-rank-arena`). Uses the bridge's relationships directly without lookup logic.

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `credential_id` | Integer | Yes | Arena OAuth client credential ID. |

**Request Example:**
```json
{
  "credential_id": 2
}
```

**Response Example:**
```json
{
  "event_bridge_id": 42,
  "arena_event_id": "abc123",
  "sge_event_id": 5,
  "sent": 12,
  "skipped": 0,
  "responses": [
    {
      "status_code": 200,
      "payload": {...},
      "response_text": "OK"
    }
  ],
  "skipped_items": []
}
```

**Logic:**
1. Fetches the EventBridge with its arena_event, sge_event, and age_group_mappings.
2. Verifies the bridge has an associated sge_event (required for sync).
3. Builds ranking payloads using the bridge's age_group_mappings for filtering.
4. For each ranking payload, POSTs to SGE API.
5. Returns summary of sent/skipped items with HTTP responses.

**Errors:**
- `400 Bad Request` if EventBridge not found or has no sge_event.
- `400 Bad Request` if `credential_id` is invalid or `ArenaIntegrationError` is raised.

> **Recommended Approach:** Use these custom actions on EventBridgeViewSet instead of the legacy arena_event_id-based views. The EventBridge pattern is cleaner because the bridge already defines the Arena event, SGE event, and age group mappings — no lookup logic needed.

---

### ArenaClientsBridgeViewSet

**Type:** `viewsets.ModelViewSet`  
**Queryset:** `ClientBridge.objects.select_related('arena_client').prefetch_related('eventos_match').all().order_by('-id')`  
**Serializers:** Dynamic based on action:
- List/Retrieve → `ArenaClientsBridgeSerializer` (nested event bridges with age group mappings)
- Create/Update/Delete → `ArenaClientsBridgeWriteSerializer`

**Basename:** `clients-match`

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/integration/bridge/clients/` | List client bridges (newest first). |
| POST | `/integration/bridge/clients/` | Create a new client bridge. |
| GET | `/integration/bridge/clients/<id>/` | Retrieve a single client bridge. |
| PUT | `/integration/bridge/clients/<id>/` | Update a client bridge (full). |
| PATCH | `/integration/bridge/clients/<id>/` | Update a client bridge (partial). |
| DELETE | `/integration/bridge/clients/<id>/` | Delete a client bridge. |

**Request Example (POST):**
```json
{
  "arena_client": 3,
  "eventos_match_ids": [42, 43]
}
```

**Response Example (GET list, single item):**
```json
{
  "id": 10,
  "arena_client": 3,
  "eventos_match": [
    {
      "id": 42,
      "nome": "Mundial U17",
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
      "sge_event": {...},
      "created_at": "2026-05-19T12:34:56Z"
    }
  ],
  "created_at": "2026-05-10T08:00:00Z"
}
```

---

### EventosSgeViewSet

**Type:** `viewsets.ReadOnlyModelViewSet`  
**Queryset:** `GestaoEventos.objects.all()`  
**Serializer:** `EventosSgeSerializer`  
**Basename:** `eventos-sge`

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/integration/eventos-sge/` | List all SGE eventos. |
| GET | `/integration/eventos-sge/<id>/` | Retrieve a single SGE evento. |

---

## APIViews (Legacy)

> **Note:** The following APIViews use arena_event_id-based lookup logic. **Prefer using the custom actions on EventosBridgeViewSet** (`/bridge/eventos/<id>/snapshot/` and `/bridge/eventos/<id>/sync-rankings/`) which work directly with EventBridge relationships.

### NormalizedRankingView

**Type:** `APIView`  
**Method:** GET  
**Path:** `/integration/normalized-ranking/<int:event_id>/`

**Purpose:** Fetches SGE fight data for a given event and enriches it with normalized weight class information from `normalization.IdClassePeso`.

**Path Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `event_id` | Integer | SGE event ID. |

**Response Example:**
```json
[
  {
    "luta_id": 123,
    "weight_class": "61 kg",
    "atleta1": 456,
    "atleta2": 789,
    "resultado": "1"
  }
]
```

**Logic:**
1. Fetch all `LutaSGE` records where `id_evento=event_id`.
2. For each fight, look up `IdClassePeso` by `id_classe_peso`.
3. If found, append `{ luta_id, weight_class, atleta1, atleta2, resultado }`.
4. If not found, skip (silent).

> ⚠ **Ambiguous:** This view does not return an error if `IdClassePeso` is missing — fights are silently omitted from the response.

---

### ArenaEventSnapshotView (Legacy)

**Type:** `APIView`  
**Method:** GET  
**Path:** `/integration/arena-events/<str:arena_event_id>/snapshot/`

**Purpose:** Builds a complete Arena event data snapshot (rankings + fights) without persisting to SGE. Uses arena_event_id lookup to find all EventBridge records.

> **Deprecated:** Use the `snapshot` action on EventosBridgeViewSet instead: `/integration/bridge/eventos/<bridge_id>/snapshot/?credential_id=X`. The bridge-based approach is cleaner because it works directly with a specific EventBridge.

**Path Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `arena_event_id` | String | Arena event UUID or identifier. |

**Query Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `credential_id` | Integer | Yes | Arena OAuth client credential ID. |
| `sge_event_id` | Integer | No | Explicit SGE event ID (overrides mapping resolution). |

**Request Example:**
```
GET /integration/arena-events/abc123/snapshot/?credential_id=2&sge_event_id=5
```

**Response Example:**
```json
{
  "arena_event_id": "abc123",
  "rankings": [
    {
      "id_evento": 5,
      "id_evento_arena": "abc123",
      "customId": "12345",
      "fullName": "John Doe",
      "rank": "1",
      "sportName": "Wrestling",
      "sportAlternateName": "LL",
      "name": "61kg",
      "audienceName": "Sub-17",
      "id_classe_peso": 42,
      "source_category_id": "cat-101",
      "match_id": 42,
      "age_group_mapping_id": 9
    }
  ],
  "fights": [
    {
      "fight_id": "fight-xyz",
      "fight_number": "1",
      "winner_fighter_id": "fighter-1",
      "result": "VPO",
      "victory_type": "Points",
      "ranking_point_nice_name": "3",
      "weight_category_id": "cat-101",
      "weight_category_name": "61kg U17 Freestyle",
      "fighter1_name": "John Doe",
      "fighter1_custom_id": "12345",
      "fighter2_name": "Jane Smith",
      "fighter2_custom_id": "67890",
      "team1": "Team A",
      "team2": "Team B",
      "end_time": "2026-05-19T15:30:00Z"
    }
  ],
  "unresolved_rankings": []
}
```

> **Note:** The `audienceName` field now contains the primary SGE variation from the matched `AgeGroupMapping` (e.g., "Sub-17" for u17 canonical group). The `age_group_mapping_id` field provides traceability to the specific mapping used.

**Errors:**
- `400 Bad Request` if `credential_id` is invalid or if `ArenaIntegrationError` is raised (e.g., event not in bridge table).

---

### ArenaEventRankingSyncView (Legacy)

**Type:** `APIView`  
**Method:** POST  
**Path:** `/integration/arena-events/<str:arena_event_id>/sync-rankings/`

**Purpose:** Fetches Arena rankings for an event and POSTs them to the SGE ranking API. Uses arena_event_id lookup to find all EventBridge records.

> **Deprecated:** Use the `sync_rankings` action on EventosBridgeViewSet instead: `POST /integration/bridge/eventos/<bridge_id>/sync-rankings/` with `{"credential_id": X}`. The bridge-based approach is cleaner because it works directly with a specific EventBridge and its relationships.

**Path Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `arena_event_id` | String | Arena event UUID or identifier. |

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `credential_id` | Integer | Yes | Arena OAuth client credential ID. |
| `sge_event_id` | Integer | No | Explicit SGE event ID (overrides mapping resolution). |

**Request Example:**
```json
{
  "credential_id": 2,
  "sge_event_id": 5
}
```

**Response Example:**
```json
{
  "arena_event_id": "abc123",
  "sent": 12,
  "skipped": 2,
  "responses": [
    {
      "status_code": 200,
      "payload": {...},
      "response_text": "OK"
    }
  ],
  "skipped_items": [
    {
      "reason": "missing_sge_event_mapping",
      "payload": {...}
    }
  ]
}
```

**Logic:**
1. Calls `sync_event_rankings_to_sge` service.
2. For each ranking payload with a valid `id_evento`, POSTs to SGE API.
3. Skips payloads where `id_evento` is null (no mapping).
4. Returns summary of sent/skipped items with HTTP responses.

**Errors:**
- `400 Bad Request` if `credential_id` is invalid or if `ArenaIntegrationError` is raised.

---

## URL Configuration

```python
router = DefaultRouter()
router.register(r'eventos-arena', EventosArenaViewSet)
router.register(r'eventos-sge', EventosSgeViewSet)
router.register(r'bridge/eventos', EventosBridgeViewSet, basename='eventos-match')
router.register(r'bridge/clients', ArenaClientsBridgeViewSet, basename='clients-match')

urlpatterns = router.urls + [
    path('normalized-ranking/<int:event_id>/', NormalizedRankingView.as_view(), name='normalized-ranking'),
    path('arena-events/<str:arena_event_id>/snapshot/', ArenaEventSnapshotView.as_view(), name='arena-event-snapshot'),
    path('arena-events/<str:arena_event_id>/sync-rankings/', ArenaEventRankingSyncView.as_view(), name='arena-event-sync-rankings'),
]
```

**Full Endpoint Table:**

| Method | Path | View | Description |
|--------|------|------|-------------|
| GET | `/integration/eventos-arena/` | `EventosArenaViewSet` | List event bridges (read-only). |
| GET | `/integration/eventos-arena/<id>/` | `EventosArenaViewSet` | Retrieve event bridge (read-only). |
| GET | `/integration/eventos-sge/` | `EventosSgeViewSet` | List SGE eventos (read-only). |
| GET | `/integration/eventos-sge/<id>/` | `EventosSgeViewSet` | Retrieve SGE evento (read-only). |
| GET/POST/PUT/PATCH/DELETE | `/integration/bridge/eventos/` | `EventosBridgeViewSet` | Full CRUD for event bridges. |
| GET | `/integration/bridge/eventos/<id>/snapshot/` | `EventosBridgeViewSet.snapshot` | **[Recommended]** Get Arena snapshot for this bridge. |
| POST | `/integration/bridge/eventos/<id>/sync-rankings/` | `EventosBridgeViewSet.sync_rankings` | **[Recommended]** Sync rankings to SGE for this bridge. |
| GET/POST/PUT/PATCH/DELETE | `/integration/bridge/clients/` | `ArenaClientsBridgeViewSet` | Full CRUD for client bridges. |
| GET | `/integration/normalized-ranking/<event_id>/` | `NormalizedRankingView` | Normalized SGE fight data. |
| GET | `/integration/arena-events/<id>/snapshot/` | `ArenaEventSnapshotView` | **[Legacy]** Arena event snapshot (use bridge action instead). |
| POST | `/integration/arena-events/<id>/sync-rankings/` | `ArenaEventRankingSyncView` | **[Legacy]** Sync rankings (use bridge action instead). |

---

## Notes

- **Authentication/Permissions:** None explicitly set — default DRF permissions apply (typically allow all in dev).
- **Ordering:** CRUD ViewSets order by `-id` (newest first).
- **Prefetch optimization:** ViewSets use `select_related` and `prefetch_related` to minimize N+1 queries. EventBridge ViewSets prefetch `age_group_mappings` M2M relationship.
- **Error handling:** Snapshot and sync views catch `ArenaIntegrationError` and return `400 Bad Request` with error detail.
- **Age Group Mapping System:** EventBridge now uses M2M relationship to `normalization.AgeGroupMapping` for flexible age group matching. Legacy `age_group` and `sge_age_category` string fields are deprecated. See [AGE_GROUP_MAPPING_GUIDE.md](AGE_GROUP_MAPPING_GUIDE.md) for details.
- **Ranking Payloads:** The `audienceName` field in ranking payloads now contains the primary SGE variation from the matched `AgeGroupMapping`. The `age_group_mapping_id` field provides traceability to the specific mapping used for each category.
- **Bridge-Based Architecture (Recommended):** Use the custom actions on `EventosBridgeViewSet` (`snapshot` and `sync_rankings`) instead of the legacy arena_event_id-based views. The EventBridge pattern is cleaner because:
  - The bridge already defines the Arena event, SGE event, and age group mappings
  - No lookup logic needed — relationships are explicit
  - Enables syncing different age groups to different SGE events (e.g., Arena event `1f14f969-6183-65fc-8be7-09cdb158879f` can have bridge #1 for Seniors → SGE event 241, and bridge #2 for U20/U17/U15 → SGE event 242)
  - Provides clear traceability: which bridge was used for which sync operation
