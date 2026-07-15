---
description: "Use when implementing Arena API client calls, token handling, webhook-triggered fetches, and Arena entity sync flows in Django DRF. Covers Arena client patterns, request safety, and payload normalization handoff."
name: "Arena API Client Patterns"
applyTo: "backend/apps/arena/**/*.py"
---
# Arena API Client Patterns

- Keep all external Arena HTTP calls inside `backend/apps/arena/services/arena_client.py` or thin wrappers in `backend/apps/arena/services/`.
- Do not scatter raw `requests` calls across views, serializers, or models.
- Treat webhook payloads as triggers, not source of truth; fetch fresh entity state from Arena API.
- Keep webhook endpoints lightweight: validate input, route entity, delegate heavy processing to services/tasks.
- Prefer explicit timeout values for outbound HTTP calls and handle connection errors cleanly.
- Reuse shared token/header helpers (`get_headers`, token retrieval helpers) instead of rebuilding auth logic.
- Use structured logging with entity and Arena id context for every outbound fetch failure.

## Payload and Mapping Rules

- Route by `entity` and support only approved entities for this codebase.
- Resolve Arena-to-SGE binding through bridge models before downstream sync.
- If binding is missing, return an `ignored` result with a machine-readable reason.
- Normalize external fields before sending to integration/SGE layers.

## Reliability Rules

- Keep handlers idempotent for duplicate webhook deliveries.
- Fail fast for invalid payload shape, but fail soft for missing mapping (ignored, not crash).
- Return deterministic response contracts from service functions (`status`, `reason`, ids).

## Testing Expectations

- Add unit tests for entity routing, missing binding behavior, and API client error paths.
- Mock Arena HTTP responses in tests; avoid real network calls.
- Cover at least one success and one ignored/error path per supported entity.
