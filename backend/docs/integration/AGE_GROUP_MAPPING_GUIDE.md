# Age Group Mapping System

## Overview

The age group mapping system provides normalized mappings between Arena and SGE age group naming variations. This solves the problem where a single Arena event can have multiple EventBridge records mapped to different SGE events based on age groups.

## Problem Statement

**Example scenario:**
- Arena event: `1f14f969-6183-65fc-8be7-09cdb158879f`
- SGE event 241 → **Seniors only**
- SGE event 242 → **U20, U17, U15** (all youth categories)

Without normalization, it's difficult to correctly route rankings from Arena categories to the appropriate SGE event.

## Solution Architecture

### 1. AgeGroupMapping Model (normalization app)

Stores normalized mappings with arena variations and SGE equivalents:

```python
class AgeGroupMapping(models.Model):
    canonical_name = CharField  # e.g., "u17" (Arena-based identifier)
    arena_variations = JSONField  # ["u17", "U17", "U-17", "Sub-17", "Under 17", "Cadete"]
    sge_variations = JSONField  # ["Sub-17", "SUB 17", "U17", "U-17"] (first is primary)
    sort_order = IntegerField  # For display ordering
```

**Properties:**
- `primary_sge_variation` → Returns the first SGE variation (considered primary)

**Methods:**
- `matches_arena_name(arena_name)` → Case-insensitive matching against arena_variations
- `matches_sge_name(sge_name)` → Case-insensitive matching against sge_variations

### 2. EventBridge Enhancement (integration app)

Added M2M relationship to AgeGroupMapping:

```python
class EventBridge(models.Model):
    # ... existing fields ...
    age_group_mappings = ManyToManyField(AgeGroupMapping)
```

**Methods:**
- `get_arena_age_variations()` → Returns all Arena age group variations from linked mappings
- `get_sge_age_variations()` → Returns all SGE age group variations from linked mappings
- `matches_arena_category(category_name)` → Checks if a category name matches any linked mapping

### 3. Updated Ranking Build Logic

The `_build_rankings` function now:

1. Fetches all EventBridge records for the arena_event_id with prefetched age_group_mappings
2. Builds an age_group_lookup dict mapping Arena variations → (EventBridge, primary_sge_variation, age_mapping)
3. For each Arena weight category:
   - Parses the age group from category name
   - Looks up the matching EventBridge using the lookup dict
   - Skips categories with no matching EventBridge
   - Uses the correct SGE event and primary SGE age variation from the matched bridge

## Setup

### 1. Run Migrations

```bash
python manage.py migrate
```

### 2. Populate Default Mappings

```bash
python manage.py populate_age_groups
```

This creates 22 mappings covering:

**Youth Categories:**
- inf-7-8 (Infantil 7 e 8)
- u9 (Sub-9)
- inf-9-10 (Infantil 9 e 10)
- u11 (Sub-11)
- inf-11-12 (Infantil 11 e 12)
- u13 (Sub-13)
- u15 (Sub-15)
- u16 (Sub-16)
- u17 (Sub-17)
- u20 (Sub-20)
- u23 (U-23)

**Senior Category:**
- seniors (Sênior)

**Veterans Categories:**
- veterans-a through veterans-g (Veteranos A-G)
- veterans-all (Veteranos All)

**Team Categories:**
- equipes-base (Equipes Base)
- equipes-senior (Equipes Senior)

Each mapping includes multiple Arena variations and SGE variations for flexible matching.

### 3. Create EventBridge with Age Group Mappings

**Via API:**

```bash
POST /api/integration/matches/eventos/
{
  "nome": "Mundial Senior 2026",
  "arena_event": 101,
  "sge_event": 241,
  "age_group_mapping_ids": [1]  # ID of "Senior" mapping
}
```

**Via Admin:**

1. Go to `/admin/integration/eventbridge/`
2. Create/edit EventBridge
3. Select age_group_mappings from the M2M widget

## Usage Examples

### Example 1: Single Age Group Event

Arena event has only Seniors:

```python
# Create EventBridge
bridge = EventBridge.objects.create(
    nome="Mundial Senior 2026",
    arena_event=arena_event,
    sge_event=sge_event_241
)

# Link to Senior age group mapping
senior_mapping = AgeGroupMapping.objects.get(canonical_name='seniors')
bridge.age_group_mappings.add(senior_mapping)
```

When building rankings:
- Arena categories with "seniors", "Seniors", "Senior", "Sênior", etc. → routed to SGE event 241 with audienceName "Sênior" (primary SGE variation)
- Arena categories with "U20", "U17" → skipped (no matching bridge)

### Example 2: Multi-Age Group Event

Arena event has U20, U17, U15:

```python
# Create EventBridge for youth categories
bridge = EventBridge.objects.create(
    nome="Mundial Juvenil 2026",
    arena_event=arena_event,
    sge_event=sge_event_242
)

# Link multiple age group mappings
youth_mappings = AgeGroupMapping.objects.filter(
    canonical_name__in=['u20', 'u17', 'u15']
)
bridge.age_group_mappings.set(youth_mappings)
```

When building rankings:
- Arena categories with "U20", "u20", "Sub-20", etc. → routed to SGE event 242 with audienceName "Sub-20" (primary SGE variation)
- Arena categories with "U17", "u17", "Sub-17", "Cadete" → routed to SGE event 242 with audienceName "Sub-17"
- Arena categories with "U15", "u15", "Sub-15", "Infantil" → routed to SGE event 242 with audienceName "Sub-15"
- Arena categories with "Senior", "seniors" → skipped (no matching bridge)

### Example 3: Complex Multi-Bridge Event

Arena event has both Seniors and Youth in separate SGE events:

```python
# Bridge 1: Seniors → SGE 241
bridge_senior = EventBridge.objects.create(
    nome="Mundial 2026 - Senior",
    arena_event=arena_event,
    sge_event=sge_event_241
)
bridge_senior.age_group_mappings.add(
    AgeGroupMapping.objects.get(canonical_name='seniors')
)

# Bridge 2: Youth → SGE 242
bridge_youth = EventBridge.objects.create(
    nome="Mundial 2026 - Juvenil",
    arena_event=arena_event,
    sge_event=sge_event_242
)
bridge_youth.age_group_mappings.set(
    AgeGroupMapping.objects.filter(canonical_name__in=['u20', 'u17', 'u15'])
)
```

When building rankings:
- Arena "Senior", "seniors", "Sênior" categories → SGE 241 with "Sênior"
- Arena "U20", "u20", "Sub-20" categories → SGE 242 with "Sub-20"
- Arena "U17", "u17", "Sub-17", "Cadete" categories → SGE 242 with "Sub-17"
- Arena "U15", "u15", "Sub-15", "Infantil" categories → SGE 242 with "Sub-15"

## API Endpoints

### Age Group Mapping Management

```
GET    /api/normalization/age-groups/           # List all mappings
POST   /api/normalization/age-groups/           # Create mapping
GET    /api/normalization/age-groups/{id}/      # Retrieve mapping
PUT    /api/normalization/age-groups/{id}/      # Update mapping
PATCH  /api/normalization/age-groups/{id}/      # Partial update
DELETE /api/normalization/age-groups/{id}/      # Delete mapping
POST   /api/normalization/age-groups/populate_defaults/  # Populate defaults
```

### EventBridge with Age Group Mappings

```
POST /api/integration/matches/eventos/
{
  "nome": "Event Name",
  "arena_event": 101,
  "sge_event": 241,
  "age_group_mapping_ids": [1, 2, 3]
}
```

Response includes `age_group_mappings` array with full mapping details.

## Admin Interface

### AgeGroupMapping Admin

Located at `/admin/normalization/agegroupmapping/`

**Features:**
- List view shows: canonical_name, primary_sge_variation (property), sort_order, created_at
- Editable sort_order in list view
- Search by canonical_name, arena_variations, sge_variations (JSON fields)
- Ordered by sort_order, canonical_name

**Fields:**
- canonical_name: Arena-based identifier (e.g., "u17", "seniors")
- arena_variations: JSON list of Arena naming patterns
- sge_variations: JSON list of SGE naming patterns (first is primary)
- sort_order: Integer for display ordering

### EventBridge Admin

Located at `/admin/integration/eventbridge/`

**Features:**
- M2M widget for selecting age_group_mappings
- Legacy age_group and sge_age_category fields marked with help text

## Backward Compatibility

The system maintains backward compatibility:

1. **Legacy string fields** (`age_group`, `sge_age_category`) are kept but marked as deprecated in help text
2. **Fallback logic** in `matches_arena_category()` checks legacy fields if no mappings exist
3. **Migration path**: Existing EventBridge records continue to work with legacy fields

## Best Practices

1. **Use age_group_mappings** for new EventBridge records instead of legacy string fields
2. **Keep mappings consistent**: Don't mix mapping IDs and legacy strings in the same bridge
3. **Populate defaults first**: Run `populate_age_groups` before creating bridges
4. **Add custom variations**: If Arena uses non-standard age group names, add them to arena_variations

## Troubleshooting

### Rankings not appearing for certain age groups

**Check:**
1. EventBridge has correct age_group_mappings linked
2. Arena category name variation exists in mapping's arena_variations
3. Use `bridge.matches_arena_category(category_name)` to test matching

### Multiple bridges matching same category

**Resolution:**
- Each age group should map to only one EventBridge per arena_event
- Review age_group_mappings assignments across bridges

### Legacy vs new system conflicts

**Solution:**
- Clear legacy `age_group` and `sge_age_category` fields when using age_group_mappings
- Or keep them synchronized for backward compatibility

## Migration from Legacy System

### Step 1: Identify existing bridges

```python
from apps.integration.models import EventBridge
from apps.normalization.models import AgeGroupMapping

# Find bridges using legacy string fields
legacy_bridges = EventBridge.objects.filter(
    age_group__isnull=False,
    age_group_mappings__isnull=True
)
```

### Step 2: Map to normalized mappings

```python
for bridge in legacy_bridges:
    # Find matching AgeGroupMapping (case-insensitive lookup)
    for mapping in AgeGroupMapping.objects.all():
        if mapping.matches_arena_name(bridge.age_group):
            bridge.age_group_mappings.add(mapping)
            print(f"Migrated {bridge.nome}: {bridge.age_group} → {mapping.canonical_name} ({mapping.primary_sge_variation})")
            break
```
```

### Step 3: Optionally clear legacy fields

```python
# After verifying mappings work correctly
for bridge in EventBridge.objects.exclude(age_group_mappings__isnull=True):
    bridge.age_group = None
    bridge.sge_age_category = None
    bridge.save()
```

## Technical Details

### Payload Enhancement

Rankings payload now includes:
```python
{
    "id_evento": sge_event_id,
    "audienceName": sge_variation,  # From AgeGroupMapping
    "age_group_mapping_id": age_mapping.id,  # For traceability
    # ... other fields
}
```

### Performance Optimization

The lookup system uses:
- `prefetch_related('age_group_mappings')` to avoid N+1 queries
- In-memory dict lookup for O(1) category matching
- Early continue/skip for non-matching categories

### Database Schema

**normalization_agegroupmapping:**
- id (PK)
- canonical_name (unique)
- arena_variations (JSON array)
- sge_variation (varchar)
- sort_order (int)

**integration_eventbridge_age_group_mappings (M2M):**
- id (PK)
- eventbridge_id (FK)
- agegroupmapping_id (FK)
