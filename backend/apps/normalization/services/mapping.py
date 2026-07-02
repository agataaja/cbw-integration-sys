import logging

logger = logging.getLogger(__name__)


def infer_sport_alternate_name(sport_name: str) -> str:
    if sport_name == "Freestyle":
        return "FS"
    if sport_name == "Greco-Roman":
        return "GR"
    return "WW"


def normalize_audience_name(audience_name: str) -> str:
    value = (audience_name or "").strip()
    lowered = value.lower()
    if lowered == "veterans a":
        return "veterans-a"
    if lowered in {"senior", "seniors", "sênior"}:
        return "seniors"
    return value


def parse_weight_category(weight_category_full_name: str) -> dict[str, str]:
    """
    Parse weight category name from Arena API.
    
    Handles two formats:
    1. Dash-separated: "Sport - Audience - Weight" (legacy format)
    2. Space-separated: "AgeGroup Sport Weight" (Arena format, e.g., "U20 GR 82")
    """
    value = (weight_category_full_name or "").strip()
    
    # Check if dash-separated format (legacy)
    if " - " in value:
        parts = [part.strip() for part in value.split(" - ")]
        sport_name = parts[0] if len(parts) > 0 else ""
        audience_name = parts[1] if len(parts) > 1 else ""
        weight_name = parts[2] if len(parts) > 2 else ""
        return {
            "sport_name": sport_name,
            "sport_alternate_name": infer_sport_alternate_name(sport_name),
            "audience_name": normalize_audience_name(audience_name),
            "weight_name": weight_name,
        }
    
    # Space-separated format: "AgeGroup Sport Weight" (e.g., "U20 GR 82", "Seniors FS 57")
    parts = value.split()
    
    if len(parts) >= 3:
        # Format: "AgeGroup Sport Weight"
        audience_name = parts[0]
        sport_alternate_name = parts[1]
        weight_name = parts[2]
        
        # Infer full sport name from alternate
        if sport_alternate_name == "FS":
            sport_name = "Freestyle"
        elif sport_alternate_name == "GR":
            sport_name = "Greco-Roman"
        elif sport_alternate_name == "WW":
            sport_name = "Women's Wrestling"
        else:
            sport_name = sport_alternate_name
        
        return {
            "sport_name": sport_name,
            "sport_alternate_name": sport_alternate_name,
            "audience_name": normalize_audience_name(audience_name),
            "weight_name": weight_name,
        }
    
    elif len(parts) == 2:
        # Format: "Sport Weight" (no age group)
        sport_alternate_name = parts[0]
        weight_name = parts[1]
        
        if sport_alternate_name == "FS":
            sport_name = "Freestyle"
        elif sport_alternate_name == "GR":
            sport_name = "Greco-Roman"
        elif sport_alternate_name == "WW":
            sport_name = "Women's Wrestling"
        else:
            sport_name = sport_alternate_name
        
        return {
            "sport_name": sport_name,
            "sport_alternate_name": sport_alternate_name,
            "audience_name": "",
            "weight_name": weight_name,
        }
    
    # Fallback: can't parse
    return {
        "sport_name": value,
        "sport_alternate_name": infer_sport_alternate_name(value),
        "audience_name": "",
        "weight_name": "",
    }


def map_audience_name_by_name(var):
    v = (var or "").lower()

    if 'por equipes' in v and 'u15' in v:
        return 'por equipes base'
    if any(x in v for x in ['u17', 'sub17', 'sub-17', 'u-17']):
        return 'U17'
    if any(x in v for x in ['u20', 'sub20', 'sub-20', 'u-20']):
        return 'U20'
    if any(x in v for x in ['u23', 'sub23', 'sub-23', 'u-23']):
        return 'U23'
    if any(x in v for x in ['u15', 'sub15', 'sub-15', 'u-15']):
        return 'U15'
    if 'sênior' in v or 'senior' in v or 'aline silva' in v or 'seniors' in v:
        return 'seniors'
    if 'circuito' in v:
        return ''
    if 'infantil' in v:
        return 'inf'
    if 'veteranos' in v:
        return 'vet'
    if any(x in v for x in ['u16', 'sub16', 'sub-16', 'u-16']):
        return 'U16'
    return ''