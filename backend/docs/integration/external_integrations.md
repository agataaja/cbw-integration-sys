# Integration — External Integrations
App: integration  
Last documented: May 19, 2026

## Overview

The integration app orchestrates data flow between **Arena** (external OAuth-based competition management platform) and **SGE** (internal sports governance REST API). It makes HTTP calls to both systems but does NOT own the OAuth client logic (that lives in `apps.arena.services.arena_client`).

---

## Arena API Integration

**Ownership:** `apps.arena.services.arena_client` (transport layer)  
**Used by:** `integration/services/arena_sge.py`

### OAuth Authentication

Integration services rely on `arena.services.arena_client.get_headers(credentials_pk)` to obtain OAuth-signed headers. The integration app does NOT manage OAuth tokens directly.

**Flow:**
1. Integration endpoint receives `credential_id` in request.
2. Integration service calls `get_headers(credential_id)` → returns `{"Authorization": "Bearer <token>", ...}`.
3. Integration service passes headers to `get_endpoint_response(headers, endpoint, pk=credential_id)`.

---

### Endpoints Called

All Arena API calls are routed through `arena.services.arena_client.get_endpoint_response` or `get_all_fights_by_event_id`.

| Endpoint | Method | Purpose | Called From |
|----------|--------|---------|-------------|
| `weight-category/{event_id}` | GET | Fetch all weight categories for an event. | `get_weight_categories_by_sport_event_id` (used by `_build_rankings`) |
| `weight-category/get/{category_id}/ranking` | GET | Fetch ranking data for a weight category. | `_build_rankings` |
| `person/get/{person_id}` | GET | Fetch person details (including `customId`). | `_get_person_custom_id` |
| `fight/event/{event_id}` (implied) | GET | Fetch all fights for an event. | `get_all_fights_by_event_id` |

**Base URL:** Managed by `apps.arena.services.arena_client` (likely stored in `ArenaClient` model or environment variable).

---

### Request/Response Contracts

#### `weight-category/{event_id}`

**Request:**
```http
GET /weight-category/{event_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "weightCategories": [
    {
      "id": "cat-101",
      "shortName": "61kg U17 Freestyle",
      ...
    }
  ]
}
```

---

#### `weight-category/get/{category_id}/ranking`

**Request:**
```http
GET /weight-category/get/{category_id}/ranking?=
Authorization: Bearer <token>
```

**Response (variant 1: dict keyed by rank):**
```json
{
  "ranking": {
    "1": {
      "fighter": {
        "personId": "person-123",
        "fullName": "John Doe",
        "rank": "1",
        "weightCategoryFullName": "61kg U17 Freestyle",
        "sportEventId": "abc123",
        "weightCategoryCountReadyFighters": 16,
        "weightCategoryCountFights": 15
      }
    },
    "2": {...}
  }
}
```

**Response (variant 2: list):**
```json
{
  "ranking": [
    {
      "fighter": {...}
    }
  ]
}
```

**Note:** Integration uses `_iter_ranking_items` to normalize both formats into a list.

---

#### `person/get/{person_id}`

**Request:**
```http
GET /person/get/{person_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "person": {
    "id": "person-123",
    "customId": "12345",
    "fullName": "John Doe",
    ...
  }
}
```

**Purpose:** Fetch `customId` (federation-assigned athlete ID) for inclusion in SGE ranking payloads.

---

#### `fight/event/{event_id}` (via `get_all_fights_by_event_id`)

**Request:**
```http
GET /fight/event/{event_id}
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": "fight-xyz",
    "fightNumber": "1",
    "winnerFighter": "fighter-1",
    "result": "VPO",
    "victoryType": "Points",
    "rankingPointNiceName": "3",
    "sportEventWeightCategoryId": "cat-101",
    "weightCategoryFullName": "61kg U17 Freestyle",
    "fighter1FullName": "John Doe",
    "fighter1PersonId": "person-123",
    "fighter2FullName": "Jane Smith",
    "fighter2PersonId": "person-456",
    "team1AlternateName": "Team A",
    "team2AlternateName": "Team B",
    "endTime": "2026-05-19T15:30:00Z"
  }
]
```

---

## SGE API Integration

**Ownership:** `integration/services/arena_sge.py` (direct HTTP POST, not routed through `apps.sge`)

### Ranking Sync Endpoint

**URL:** `{SGE_ARENA_API_URL}/resultado-rank-arena`  
**Environment Variable:** `SGE_ARENA_API_URL` (default: `https://restcbw.bigmidia.com/cbw/api`)  
**Method:** POST  
**Content-Type:** `application/json`  
**Timeout:** 30 seconds

---

### Request Contract

**Payload (per fighter):**
```json
{
  "id_evento": 5,
  "id_evento_arena": "abc123",
  "countFighters": "16",
  "countFights": "15",
  "weightCategoryFullName": "61kg U17 Freestyle",
  "customId": "12345",
  "fullName": "John Doe",
  "rank": "1",
  "sportAlternateName": "LL",
  "sportName": "Wrestling Freestyle",
  "name": "61kg",
  "audienceName": "SUB 17",
  "id_classe_peso": 42,
  "source_category_id": "cat-101",
  "match_id": 42
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id_evento` | Integer | Yes | SGE event ID (from `EventBridge.sge_event_id`). |
| `id_evento_arena` | String | Yes | Arena event ID. |
| `countFighters` | String | No | Total fighters in weight category. |
| `countFights` | String | No | Total fights in weight category. |
| `weightCategoryFullName` | String | Yes | Original Arena weight category name. |
| `customId` | String | No | Federation-assigned athlete ID (from Arena person). |
| `fullName` | String | Yes | Fighter's full name. |
| `rank` | String | Yes | Rank position (e.g., "1", "2"). |
| `sportAlternateName` | String | Yes | SGE sport code (e.g., "LL" for Freestyle, "LG" for Greco-Roman). |
| `sportName` | String | Yes | Parsed sport name. |
| `name` | String | Yes | Parsed weight class name (e.g., "61kg"). |
| `audienceName` | String | Yes | Normalized age group (e.g., "SUB 17"). |
| `id_classe_peso` | Integer | No | SGE weight class ID (from `normalization.IdClassePeso`). |
| `source_category_id` | String | No | Arena weight category ID (for traceability). |
| `match_id` | Integer | No | EventBridge ID (for traceability). |

---

### Response Contract

**Status Codes:**
- `200 OK` — Ranking successfully saved.
- `400 Bad Request` — Invalid payload (missing required fields).
- `500 Internal Server Error` — SGE API error.

**Response Body:** Plain text or JSON (contract not documented by SGE team).

**Integration Handling:**  
Integration services capture `response.status_code` and `response.text` for each POST and return them in the sync summary.

---

### Error Handling

Integration does NOT retry on failure. If SGE API returns non-200 status, the response is logged in the `responses` array but NO exception is raised.

**Example sync result with failure:**
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
    },
    {
      "status_code": 500,
      "payload": {...},
      "response_text": "Internal Server Error"
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

---

## SGE Eventos Fetch (via Arena Integration Module)

**URL:** `{SGE_GESTAO_API_URL}/...` (exact endpoint not visible in integration code)  
**Environment Variable:** `SGE_GESTAO_API_URL` (default: `https://restcbw.bigmidia.com/cbw/gestao`)  
**Ownership:** `apps.arena.integrations.sge_rest_api.get_all_sge_eventos_info`

**Purpose:** Fetch SGE eventos for display/mapping in integration UI.

**Called by:** `integration/services/sge_events.process_eventos_sge`

> ⚠ **Architectural note:** This function lives in `apps.arena.integrations.sge_rest_api`, which is a boundary crossing. SGE API calls should ideally be in `apps.sge` or `apps.integration`, not `apps.arena`.

---

## Webhook Integration

Integration does NOT receive webhooks directly. Arena webhooks are received by `apps.arena.webhook.*` and routed into integration logic.

**Flow:**
1. Arena POSTs webhook to `/arena/webhook/<client_id>/`.
2. Arena webhook handler (`apps.arena.webhook.*`) parses payload.
3. Webhook handler checks/creates `EventBridge` via `integration.models.EventBridge`.
4. Webhook handler triggers integration sync (optional, depends on webhook type).

**Webhook payload contract:** See `apps.arena` webhook documentation.

---

## Summary Table

| External System | Endpoint | Method | Purpose | Owner | Auth |
|-----------------|----------|--------|---------|-------|------|
| Arena API | `weight-category/{event_id}` | GET | Fetch weight categories. | `arena.services.arena_client` | OAuth 2.0 |
| Arena API | `weight-category/get/{id}/ranking` | GET | Fetch rankings. | `arena.services.arena_client` | OAuth 2.0 |
| Arena API | `person/get/{id}` | GET | Fetch person details. | `arena.services.arena_client` | OAuth 2.0 |
| Arena API | `fight/event/{id}` | GET | Fetch fights. | `arena.services.arena_client` | OAuth 2.0 |
| SGE API | `/resultado-rank-arena` | POST | Sync rankings to SGE. | `integration.services.arena_sge` | None (public) |
| SGE Gestao API | (undocumented) | GET | Fetch SGE eventos. | `arena.integrations.sge_rest_api` | None (public) |

---

## Notes

- **OAuth delegation:** Integration services do NOT manage OAuth tokens — they delegate to `apps.arena.services.arena_client.get_headers`.
- **No retry logic:** Arena and SGE API calls do NOT retry on failure (except as implemented in `arena.services.arena_client`).
- **Timeout:** SGE ranking POST has a 30-second timeout; Arena API timeouts are managed by `arena.services.arena_client`.
- **Error propagation:** Arena API errors raise `ArenaIntegrationError`; SGE API errors are logged but NOT raised (sync returns partial success).
