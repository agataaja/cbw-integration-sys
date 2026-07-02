# Integration — Models
App: integration  
Last documented: May 20, 2026

## Overview

The integration app provides cross-domain bridge models that map entities between the **Arena** platform (external competition management) and **SGE** (internal sports governance engine). These models represent many-to-many or one-to-many relationships where a single Arena entity may correspond to multiple SGE entities, especially across age groups or event categories.

---

## Models

### EventBridge

**Purpose:** Maps an Arena sport event to one or more SGE eventos, optionally segmented by age group and SGE age category. A single Arena event can have multiple `EventBridge` records if it spans multiple age groups, each mapped to a distinct SGE evento.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `BigAutoField` | Primary Key | Unique identifier. |
| `nome` | `CharField(255)` | — | Descriptive name for the mapping entry. |
| `age_group` | `CharField(255)` | Nullable, Blank | **DEPRECATED.** Legacy Arena-side age group identifier. Use `age_group_mappings` instead. |
| `sge_age_category` | `CharField(255)` | Nullable, Blank | **DEPRECATED.** Legacy SGE-side normalized age category. Use `age_group_mappings` instead. |
| `age_group_mappings` | `ManyToManyField(AgeGroupMapping)` | Blank | Normalized age group mappings from `normalization.AgeGroupMapping`. Links this bridge to one or more age group variations. |
| `sge_event` | `ForeignKey(GestaoEventos)` | Cascade | Reference to the SGE evento record. |
| `arena_event` | `ForeignKey(ArenaSportEvent)` | Cascade | Reference to the Arena sport event. |
| `created_at` | `DateTimeField` | Auto-add | Timestamp when the bridge was created. |

**Methods:**
- `get_arena_age_variations()` → Returns list of all Arena age group name variations from linked `age_group_mappings`.
- `get_sge_age_variations()` → Returns list of all SGE age group variations from linked `age_group_mappings`.
- `matches_arena_category(category_name)` → Returns `True` if the category name matches any linked age group mapping.

**Meta:**
- `unique_together = (('arena_event', 'age_group', 'sge_event', 'sge_age_category'))` — ensures one bridge per Arena event + age group + SGE event + SGE age category combination (legacy constraint, maintained for backward compatibility).

**Related Names:**
- `GestaoEventos.evento_sge_origin` → all EventBridge instances pointing to this SGE evento.
- `ArenaSportEvent.evento_arena_origin` → all EventBridge instances for this Arena event.

**Domain Meaning:**  
A single Arena wrestling competition may include U15, U17, and Senior brackets. Each age bracket maps to a separate `GestaoEventos` in SGE, so this event would have three `EventBridge` records. The new `age_group_mappings` M2M field allows flexible age group matching using normalized mappings from `normalization.AgeGroupMapping`, supporting multiple naming variations (e.g., "U17", "Sub-17", "Under 17" all map to the same canonical group).

**Migration from Legacy Fields:**  
Legacy `age_group` and `sge_age_category` string fields are deprecated. New implementations should use `age_group_mappings` M2M relationship. See [AGE_GROUP_MAPPING_GUIDE.md](AGE_GROUP_MAPPING_GUIDE.md) for migration details.

---

### ClientBridge

**Purpose:** Maps an Arena client (OAuth credential holder) to a set of event bridges, representing which SGE eventos are accessible/synced under that client's Arena credentials.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `BigAutoField` | Primary Key | Unique identifier. |
| `arena_client` | `ForeignKey(ArenaClient)` | Cascade | Reference to the Arena OAuth client. |
| `eventos_match` | `ManyToManyField(EventBridge)` | Blank | Set of event bridges associated with this client. |
| `created_at` | `DateTimeField` | Auto-add | Timestamp when the bridge was created. |

**Related Names:**
- `ArenaClient.arena_client_origin` → all ClientBridge instances for this client.
- `EventBridge.arena_client_eventos_match_origin` → all ClientBridge instances referencing this event bridge.

**Domain Meaning:**  
One Arena client (e.g., a national federation's OAuth app) can manage multiple events. This model tracks which event bridges are under a specific client's purview.

---

### AthleteBridge

**Purpose:** Maps Arena person/athlete/fighter representations to a single SGE athlete (`GestaoAtletas`) and their associated IDs (`GestaoIdsAtletas`). Arena maintains multiple entities for the same person (person, athlete, fighter), while SGE has a unified athlete record.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `BigAutoField` | Primary Key | Unique identifier. |
| `nome` | `CharField(255)` | — | Athlete's name for reference. |
| `sge_id_atleta` | `ForeignKey(GestaoAtletas)` | Cascade | SGE athlete record (main athlete data). |
| `sge_id` | `ForeignKey(GestaoIdsAtletas)` | Cascade | SGE athlete IDs record (ID mappings, e.g., federation IDs). |
| `arena_custom_id` | `ForeignKey(ArenaPerson)` | Cascade, Nullable | Arena person entity (optional link). |
| `arena_athlete` | `ManyToManyField(ArenaAthlete)` | Blank | Arena athlete entities linked to this SGE athlete. |
| `arena_fighter` | `ManyToManyField(ArenaFighter)` | Blank | Arena fighter entities (competition-specific athlete instances) linked to this SGE athlete. |
| `created_at` | `DateTimeField` | Auto-add | Timestamp when the bridge was created. |

**Related Names:**
- `GestaoAtletas.atleta_sge_origin` → all AthleteBridge instances for this SGE athlete.
- `GestaoIdsAtletas.id_atleta_sge_origin` → all AthleteBridge instances for this SGE ID record.
- `ArenaPerson.atleta_arena_origin` → all AthleteBridge instances for this Arena person.
- `ArenaAthlete.atleta_arena_athlete_origin` → all AthleteBridge instances referencing this Arena athlete.
- `ArenaFighter.atleta_arena_fighter_origin` → all AthleteBridge instances referencing this Arena fighter.

**Domain Meaning:**  
A wrestler in SGE has one `GestaoAtletas` record and one `GestaoIdsAtletas` record. In Arena, the same person may have multiple `ArenaFighter` records (one per event they compete in) and one `ArenaPerson` record. This bridge consolidates these many-to-one relationships.

---

### FightBridge

**Purpose:** Maps an Arena fight (match/bout) to an SGE fight record (`LutaSGE`). Used for result synchronization and historical match tracking.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `BigAutoField` | Primary Key | Unique identifier. |
| `nome` | `CharField(255)` | — | Descriptive name for the fight mapping. |
| `sge_luta` | `ForeignKey(LutaSGE)` | Cascade | SGE fight record. |
| `arena_fight` | `ForeignKey(ArenaFight)` | Cascade, Nullable | Arena fight record (null if SGE-originated fight). |
| `created_at` | `DateTimeField` | Auto-add | Timestamp when the bridge was created. |

**Related Names:**
- `LutaSGE.luta_sge_origin` → all FightBridge instances for this SGE fight.
- `ArenaFight.luta_arena_origin` → all FightBridge instances for this Arena fight.

**Domain Meaning:**  
Arena and SGE both store match/fight results. This bridge ensures that a fight in Arena can be traced to its corresponding SGE record (or vice versa).

---

## Legacy Aliases

The following aliases exist for backward compatibility with older imports:

| Alias | Canonical Model |
|-------|-----------------|
| `EventosMatch` | `EventBridge` |
| `ArenaClientsMatch` | `ClientBridge` |
| `AtletaMatch` | `AthleteBridge` |
| `LutaMatch` | `FightBridge` |

> **Note:** These aliases are temporary. All new code should reference the canonical `*Bridge` names.

---

## Notes

- **Age-group segmentation** is critical: a single Arena event can map to multiple SGE eventos if it has multiple age brackets. Use the `EventBridge.age_group_mappings` M2M field to link to normalized age group mappings. Legacy `age_group` and `sge_age_category` string fields are deprecated.
- **Normalized age group mappings** (via `normalization.AgeGroupMapping`) provide flexible matching of Arena and SGE age group naming variations. 22 standard mappings are available covering youth (u9-u23), seniors, veterans, and team categories.
- **Unique constraints** prevent duplicate mappings for the same Arena event + age group + SGE event combination (legacy constraint).
- All bridges use `CASCADE` delete semantics: if an Arena or SGE entity is deleted, the bridge is automatically removed.
- See [AGE_GROUP_MAPPING_GUIDE.md](AGE_GROUP_MAPPING_GUIDE.md) for comprehensive age group mapping system documentation.
