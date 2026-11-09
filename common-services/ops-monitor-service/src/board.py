# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What the screen shows besides the live feed, rebuilt in the background from state tables (read-only):

    places   rows of one table (the deployment says which) placed on the map, with per-place counts
    kpis     headline numbers: count (or sum of a field) of rows matching a criteria
    services every service's heartbeat (up / stale, counters)

All of it comes from the deployment file's `monitor:` section, so the code never knows what a place or a number
means for one product. `{today}` in a criteria is today's date in the deployment's time zone.
"""
from __future__ import annotations

import logging
import threading
import time
from collections import Counter
from typing import Any, Optional

from geocode import Geocoder

logger = logging.getLogger(__name__)


def today() -> str:
    from grepx_service import today_iso
    return today_iso()


def fill(criteria: Optional[str], day: str) -> str:
    return (criteria or "").replace("{today}", day)


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class Board:
    def __init__(self, settings: dict, reader: Any, geocoder: Geocoder, day=today):
        self.settings, self.reader, self.geocoder, self.day = settings or {}, reader, geocoder, day
        self.lock = threading.Lock()
        self.data: dict = {"places": [], "kpis": [], "services": [], "updated": {}}

    # ---- pieces ----
    def places(self) -> list[dict]:
        spec = self.settings.get("places") or {}
        if not spec.get("table"):
            return []
        day = self.day()
        rows = self.reader.accepted(spec["table"], fill(spec.get("where"), day))
        counts = {}
        for c in spec.get("counts") or []:
            hits = self.reader.accepted(c["table"], fill(c.get("where"), day))
            counts[c["name"]] = Counter(str(r.get(c["by"]) or "") for r in hits)
        out = []
        for r in rows:
            pid = str(r.get(spec.get("id") or "") or r.get("_key") or "")
            address = str(r.get(spec.get("address") or "") or "")
            point = self.geocoder.locate(address)
            out.append({"id": pid, "label": str(r.get(spec.get("label") or "") or pid), "address": address,
                        "date": str(r.get(spec.get("date") or "") or ""), "capacity": _number(r.get(spec.get("capacity") or "")),
                        "lng": point[0] if point else None, "lat": point[1] if point else None,
                        "counts": {name: c.get(pid, 0) for name, c in counts.items()}})
        return sorted(out, key=lambda p: (p["date"], p["label"]))

    def kpis(self) -> list[dict]:
        day, out = self.day(), []
        for k in self.settings.get("kpis") or []:
            rows = self.reader.accepted(k["table"], fill(k.get("where"), day))
            value = sum(_number(r.get(k["sum"])) for r in rows) if k.get("sum") else len(rows)
            out.append({"label": k.get("label") or k["table"], "value": int(value) if float(value).is_integer() else round(value, 1),
                        "of": k.get("of"), "hint": k.get("hint", "")})
        return out

    def services(self) -> list[dict]:
        from nexus_api import HEALTH_TABLE, is_stale
        keep = ("service", "project", "port", "started_at", "last_seen", "handled", "accepted", "rejected", "errors", "last_error")
        rows = [{**{k: r.get(k) for k in keep}, "up": not is_stale(str(r.get("last_seen") or ""))}
                for r in self.reader.rows(HEALTH_TABLE)]
        return sorted(rows, key=lambda s: str(s.get("service") or ""))

    # ---- refresh loop ----
    def refresh(self, part: str) -> None:
        try:
            value = getattr(self, part)()
        except Exception as exc:          # one failing table must not blank the rest of the screen
            logger.warning("refresh %s failed: %s", part, exc)
            return
        with self.lock:
            self.data[part] = value
            self.data["updated"][part] = time.time()

    def snapshot(self) -> dict:
        with self.lock:
            return {k: (dict(v) if isinstance(v, dict) else list(v)) for k, v in self.data.items()}

    def start(self, every: Optional[dict] = None) -> "Board":
        every = {"services": 5, "kpis": 15, "places": 30, **(every or {})}

        def loop(part: str, seconds: float) -> None:
            while True:
                self.refresh(part)
                time.sleep(seconds)
        for part, seconds in every.items():
            threading.Thread(target=loop, args=(part, seconds), daemon=True, name=f"board-{part}").start()
        return self
