---
description: "Use when implementing or updating SGE integration contracts, Arena-to-SGE bridge logic, and event synchronization services. Covers contract validation, mapping invariants, and error semantics for integration services."
name: "SGE Integration Contracts"
applyTo: "backend/apps/integration/services/**/*.py"
---
# SGE Integration Contracts

- Keep contract translation in service layer code under `backend/apps/integration/services/`.
- Treat SGE payload contracts as strict: map fields explicitly and avoid pass-through of raw Arena structures.
- Use bridge models as source of identity mapping truth (`EventBridge`, `ClientBridge` and related entities).
- If required mapping does not exist, return `ignored` with clear reason; do not fabricate ids.

## Contract Design Rules

- Keep request payload builders deterministic and explicit.
- Preserve stable keys and value types expected by SGE endpoints.
- Convert date/time fields to the exact format expected by SGE before outbound calls.
- Validate required fields before sending requests to SGE APIs.

## Error and Logging Rules

- Log integration failures with enough correlation data (entity, arena_event_id, sge_event_id when available).
- Raise domain-specific errors for unrecoverable contract issues; use structured result objects for soft failures.
- Do not implement hidden retry loops in request handlers; surface failure clearly.

## Integration Flow Rules

- Resolve mapping first, fetch/prepare data second, normalize third, call SGE last.
- Keep normalization logic delegated to `normalization` services; avoid duplicate transformation code.
- Separate orchestration from transport details so SGE client behavior can be tested independently.

## Testing Expectations

- Add tests for contract field mapping, required field validation, and missing bridge behavior.
- Mock outbound SGE calls and assert payload shape.
- Cover success path and at least one explicit failure/ignored path per service entry point.
