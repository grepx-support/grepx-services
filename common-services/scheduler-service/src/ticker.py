"""Ticker — every interval, emit one `ticks` row per due slot (deterministic key ⇒ fires once)."""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime
from typing import Callable

from grepx_service import Emitter, Reader
from grepx_service.wire import local_tz

from domain import due_slot
from dto import SCHEDULES_TABLE, TICKS_TABLE, ScheduleField as F

logger = logging.getLogger(__name__)


class Ticker:
    def __init__(self, app, cfg, clock: Callable[[], datetime] = lambda: datetime.now(local_tz())):
        self.read, self.emitter, self.clock = Reader(app.client), Emitter(app, cfg), clock

    def tick(self) -> int:
        fired = 0
        now = self.clock()
        for s in self.read.accepted(SCHEDULES_TABLE):
            slot = due_slot(s.get(F.KIND.value, ""), now, int(s.get(F.EVERY_MINUTES.value) or 0), s.get(F.AT.value, ""))
            if not slot:
                continue
            key = f"{s['_key']}-{slot}"
            if self.read.one(TICKS_TABLE, key):
                continue
            if self.emitter.request(TICKS_TABLE, key, {F.SCHEDULE_ID.value: s["_key"], F.JOB.value: s.get(F.JOB.value),
                                                       F.SLOT.value: slot}, s.get(F.TARGET_SERVICE.value)):
                fired += 1
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
