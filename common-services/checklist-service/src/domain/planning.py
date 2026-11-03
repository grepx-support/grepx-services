"""Turn a template item into a dated task. Pure."""
import hashlib
from datetime import date, timedelta


def due_at(base_date: str, days: int, time: str = "09:00") -> str:
    return f"{date.fromisoformat(base_date) + timedelta(days=int(days)):%Y-%m-%d}T{time or '09:00'}"


def stable_id(*parts: str) -> str:
    """Same ref + title ⇒ same task id, so applying a checklist twice never duplicates."""
    return hashlib.sha1("|".join(parts).encode()).hexdigest()[:24]
