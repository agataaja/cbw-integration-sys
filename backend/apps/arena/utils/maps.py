import pandas as pd


def map_audience_name_by_name(var):

    v = var.lower()

    if 'por equipes' in var and 'u15' in var:
        return 'por equipes base'
    elif any(x in v for x in ['u17', 'sub17', 'sub-17', 'u-17']):
        return 'U17'
    elif any(x in v for x in ['u20', 'sub20', 'sub-20', 'u-20']):
        return 'U20'
    elif any(x in v for x in ['u23', 'sub23', 'sub-23', 'u-23']):
        return 'U23'
    elif any(x in v for x in ['u15', 'sub15', 'sub-15', 'u-15']):
        return 'U15'
    elif 'sênior' in v or 'senior' in v or 'aline silva' in v or 'seniors' in v:
        return 'seniors'
    elif 'circuito' in v:
        return ''
    elif 'infantil' in v:
        return 'inf'
    elif 'veteranos' in v:
        return 'vet'
    elif any(x in v for x in ['u16', 'sub16', 'sub-16', 'u-16']):
        return 'U16'
    else:
        return 'foda em'



