# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Ticker - every interval, emit one `ticks` row per due slot (deterministic key => fires once), skip paused schedules,
note on each schedule when it last fired and its next times, and leave a heartbeat (HEALTH reads it)."""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime
from typing import Callable

from grepx_service import Emitter, Reader
from grepx_service.wire import local_tz

from dto import HEALTH_TABLE, SCHEDULES_TABLE, TICKS_TABLE, ScheduleField as F
from routes.common import described, plain, rule
from routes.run_now import ticket

logger = logging.getLogger(__name__)


def _since(s: dict):
    text = str(s.get(F.SINCE.value) or "")
    return datetime.fromisoformat(text) if text else None


class Ticker:
    def __init__(self, app, cfg, clock: Callable[[], datetime] = lambda: datetime.now(local_tz())):
        self.read, self.emitter, self.clock = Reader(app.client), Emitter(app, cfg), clock

    def due(self, s: dict, now: datetime):
        if s.get(F.PAUSED.value):
            return None
        try:
            return rule(s).due(now, _since(s))
        except ValueError:
            logger.warning("schedule %s has a rule that is not valid - skipped", s.get("_key"))
            return None

    def tick(self) -> int:
        fired, now = 0, self.clock()
        for row in self.read.accepted(SCHEDULES_TABLE):
            s = plain(row)
            slot = self.due(s, now)
            key = f"{row['_key']}-{slot}"
            if not slot or self.read.one(TICKS_TABLE, key):
                continue
            if self.emitter.request(TICKS_TABLE, key, ticket(s, slot), s.get(F.TARGET_SERVICE.value)):
                fired += 1
                self.emitter.submit(SCHEDULES_TABLE, row["_key"], "ACCEPTED", described({**s, F.LAST_FIRED.value: slot}, now))
        self.emitter.submit(HEALTH_TABLE, "ticker", "ACCEPTED", {"at": now.timestamp()})
        return fired

    def run_forever(self, interval: float = 20.0) -> threading.Thread:
        def loop():
            while True:
                try:
                    self.tick()
                except Exception:
                    logger.exception("tick failed")
                time.sleep(interval)
        thread = threading.Thread(target=loop, daemon=True)
        thread.start()
        return thread


def start(cfg) -> None:
    """on_start hook (config.yaml): tick in the background while the service handles its requests."""
    from nexus_api import create_app
    Ticker(create_app("scheduler-ticker", "ticks", host=cfg.nexus.host, port=cfg.nexus.port), cfg).run_forever(cfg.get("tick_seconds", 20))
