# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Wiring: one Monitor per process - the feed, the board, who may look - and the tables it watches.

Watched: every service's request table (from grepx_contracts, so a new service is watched without a change here),
dead letters, and any `monitor.watch` tables the deployment adds. The monitor only reads: it subscribes and selects,
it never submits a row.
"""
from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from access import Access
from board import Board
from feed import DEAD, Feed
from geocode import Geocoder

_lock = threading.Lock()
_monitor: Optional["Monitor"] = None


class Monitor:
    def __init__(self, cfg: Any, client: Any = None, store: Any = None):
        import logging
        from grepx_service import Reader
        # the board polls tables every few seconds: keep row contents (names, phones…) out of this service's log
        logging.getLogger("nexus_api.impl.tcp_connection").setLevel(logging.WARNING)
        self.cfg = cfg
        self.settings = dict(cfg.get("monitor") or {})
        places = self.settings.get("places") or {}
        refs = list(self.settings.get("refs") or ([places["id"]] if places.get("id") else []))
        self.feed = Feed(size=int(self.settings.get("window") or 5000), refs=refs)
        if client is None:
            from nexus_api import NexusClient
            client = NexusClient(f"{cfg.service_name}-reader", host=cfg.nexus.host, port=cfg.nexus.port)
        if store is None:
            from grepx_store import store_for
            store = store_for(cfg)
        self.reader = Reader(client)
        geo = self.settings.get("map") or {}
        self.board = Board(self.settings, self.reader,
                           Geocoder(geo.get("geocoder") or "none", geo.get("country") or "", places.get("known"), store))
        self.access = Access(cfg, self.reader)
        self.started = time.time()

    def tables(self) -> list[str]:
        import grepx_contracts as gc
        found = [getattr(gc, name).REQUESTS for name in gc.__all__ if getattr(getattr(gc, name), "REQUESTS", "")]
        return list(dict.fromkeys([*found, DEAD, *(self.settings.get("watch") or [])]))

    def public_config(self) -> dict:
        """What the page needs to draw itself (no data)."""
        s = self.settings
        return {"title": s.get("title") or "Live", "subtitle": s.get("subtitle") or "", "map": {k: v for k, v in (s.get("map") or {}).items()
                                                                                          if k in ("center", "zoom", "style", "bounds")},
                "words": s.get("words") or {}, "counts": [c.get("name") for c in (s.get("places") or {}).get("counts") or []],
                "accent": s.get("accent") or "", "tables": self.tables()}

    def on_row(self, table: str, key: str, fields: dict) -> None:
        when = str(fields.get("occurred_at") or "")
        old = False
        try:
            old = datetime.fromisoformat(when).timestamp() < self.started - 5
        except ValueError:
            pass
        self.feed.add(table, key, fields, recovered=old)


def monitor(cfg: Any) -> Monitor:
    global _monitor
    with _lock:
        if _monitor is None:
            _monitor = Monitor(cfg)
        return _monitor


def subscriptions(cfg: Any) -> list:
    """config.yaml `discover:` - one subscription per watched table; recent history first, then live."""
    from grepx_service.runner import Subscription
    m = monitor(cfg)
    m.board.start()
    hours = float(m.settings.get("history_hours") or 6)
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")
    return [Subscription(t, lambda app, row, cfg, t=t: m.on_row(t, row.key, dict(row.fields)), "", f"occurred_at > '{since}'")
            for t in m.tables()]
