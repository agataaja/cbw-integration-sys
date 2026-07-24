from datetime import datetime


def format_datetime(dt):

    if not dt:
        return "1900-01-01 00:00:00"

    if isinstance(dt, str):
        try:
            # tenta converter ISO8601 (com T, timezone, etc.)
            parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            # se for string simples já no formato YYYY-MM-DD HH:MM:SS
            if len(dt) >= 19:  # "2025-02-15 16:05:38"
                return dt[:19]
            return "1900-01-01 00:00:00"

    # se for datetime de verdade
    return dt.strftime("%Y-%m-%d %H:%M:%S")