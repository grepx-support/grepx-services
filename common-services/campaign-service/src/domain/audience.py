"""Who receives a campaign. Pure: people + per-person stats + roles in, people out.

Generic audiences: the member role (everyone who is not staff) and each staff role by name.
A product adds its own audiences and invite filters through its audience plugin (config plugins.audience).
"""
from __future__ import annotations

from datetime import date
from typing import Any, Optional


class AudienceError(ValueError):
    pass


def resolve_audience(name: str, people: list[dict], stats: dict, roles: dict, today: date, member_role: str,
                     product: Optional[Any] = None) -> list[dict]:
    if name in (member_role, "member"):
        return [p for p in people if roles.get(p["_key"], member_role) == member_role]
    if name in set(roles.values()):
        return [p for p in people if roles.get(p["_key"]) == name]
    picked = product.audience(name, people, stats, roles, today, member_role) if product is not None else None
    if picked is None:
        raise AudienceError("UNKNOWN_AUDIENCE")
    return picked


def matches_filters(person: dict, stats: dict, filters: dict, today: date, product: Optional[Any] = None) -> bool:
    if person["_key"] in set(filters.get("exclude") or []):
        return False
    return product.matches(person, stats, filters, today) if product is not None else True
