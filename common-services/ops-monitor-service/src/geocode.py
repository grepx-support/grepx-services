# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Address text -> map coordinates, cached in this service's own database.

Strategy chosen by the deployment (`monitor.map.geocoder`): onemap (Singapore's free OneMap search), nominatim
(OpenStreetMap, any country; `monitor.map.country` narrows it), or none. `monitor.places.known` pins an address
(or any text it contains) to fixed coordinates and always wins. Lookups run on the background refresh, never while a
page waits; a miss is remembered for a day so a bad address is not asked for again every minute.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import time
import urllib.parse
import urllib.request
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)
CACHE = "geo_cache"
MISS_RETRY_S = 24 * 3600
FAIL_PAUSE_S = 600                   # after a network failure, wait this long before asking again
AGENT = "GrepX-ops-monitor/1.0"

Point = tuple[float, float]          # (lng, lat), the order map libraries use


def fetch_json(url: str, timeout: float = 6.0) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:      # noqa: S310 - fixed https hosts below
        return json.loads(response.read().decode("utf-8"))


def onemap(query: str, get: Callable[[str], Any] = fetch_json, country: str = "") -> Optional[Point]:
    url = "https://www.onemap.gov.sg/api/common/elastic/search?" + urllib.parse.urlencode(
        {"searchVal": query, "returnGeom": "Y", "getAddrDetails": "N", "pageNum": 1})
    hits = (get(url) or {}).get("results") or []
    return (float(hits[0]["LONGITUDE"]), float(hits[0]["LATITUDE"])) if hits else None


def nominatim(query: str, get: Callable[[str], Any] = fetch_json, country: str = "") -> Optional[Point]:
    params = {"q": query, "format": "json", "limit": 1}
    if country:
        params["countrycodes"] = country.lower()
    hits = get("https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)) or []
    return (float(hits[0]["lon"]), float(hits[0]["lat"])) if hits else None


STRATEGIES = {"onemap": onemap, "nominatim": nominatim}


def attempts(address: str) -> list[str]:
    """What to search for, most precise first: a 6-digit postal code, the whole text, then its first part."""
    text = " ".join(str(address).split())
    tries = re.findall(r"\b\d{6}\b", text) + [text]
    head = re.split(r"[,(\n]", text)[0].strip()
    if head and head != text:
        tries.append(head)
    return list(dict.fromkeys(t for t in tries if t))


class Geocoder:
    def __init__(self, strategy: str = "none", country: str = "", known: Optional[dict] = None, store: Any = None,
                 get: Callable[[str], Any] = fetch_json, clock: Callable[[], float] = time.time):
        self.lookup = STRATEGIES.get((strategy or "none").lower())
        self.country, self.store, self.get, self.clock = country, store, get, clock
        self.paused_until = 0.0
        self.known = {str(k).lower(): (float(v[0]), float(v[1])) for k, v in (known or {}).items()}

    def locate(self, address: str) -> Optional[Point]:
        if not address:
            return None
        lowered = str(address).lower()
        for text, point in self.known.items():
            if text in lowered:
                return point
        key = hashlib.sha1(lowered.encode()).hexdigest()
        cached = self.store.get(CACHE, key) if self.store is not None else None
        if cached and cached.get("lng") is not None:
            return float(cached["lng"]), float(cached["lat"])
        if cached and self.clock() - float(cached.get("checked") or 0) < MISS_RETRY_S:
            return None
        if self.lookup is None or self.clock() < self.paused_until:
            return None
        point = None
        for query in attempts(address):
            try:
                point = self.lookup(query, self.get, self.country)
            except Exception as exc:                 # network down, rate limited, odd reply: try again on a later refresh
                logger.warning("geocode failed for %r: %s (next try in %d min)", query, exc, FAIL_PAUSE_S // 60)
                self.paused_until = self.clock() + FAIL_PAUSE_S
                return None
            if point:
                break
        if self.store is not None:
            self.store.put(CACHE, key, {"address": str(address)[:200], "lng": point[0] if point else None,
                                        "lat": point[1] if point else None, "checked": self.clock()})
        return point
