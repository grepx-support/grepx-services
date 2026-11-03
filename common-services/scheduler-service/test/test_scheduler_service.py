"""scheduler-service: schedule validation, due slots, ticks fire exactly once per slot."""
from datetime import datetime
from pathlib import Path

import pytest
from grepx_testkit.harness import ServiceHarness
from nexus_api import NexusApplication
from grepx_config import load_config
from nexus_testkit import MemoryClient

from domain import due_slot
from routes import handle
from ticker import Ticker

cfg = load_config(Path(__file__).resolve().parents[1] / "config")


@pytest.fixture()
def h():
    return ServiceHarness().add(cfg, "schedule_requests", handle, cfg.live_criteria)


def register(h, **f):
    return h.call("schedule_requests", "scheduler-service", {"action": "REGISTER", "schedule_id": "s1", "job": "j",
                                                              "target_service": "x-service", **f})


def test_invalid_schedule_should_reject(h):
    assert register(h, kind="DAILY_AT").reason == "INVALID_SCHEDULE"


def test_daily_schedule_should_tick_once_per_day(h):
    assert register(h, kind="DAILY_AT", at="09:00").ok
    app = NexusApplication(MemoryClient(h.engine), "ticks")
    morning = Ticker(app, cfg, clock=lambda: datetime(2026, 1, 5, 8, 0))
    later = Ticker(app, cfg, clock=lambda: datetime(2026, 1, 5, 10, 0))
    assert morning.tick() == 0 and later.tick() == 1 and later.tick() == 0
    tick = h.rows("ticks")[0]
    assert tick["to_service"] == "x-service" and tick["job"] == "j" and tick["status"] == "NEW"


@pytest.mark.parametrize("now,expected", [(datetime(2026, 1, 1, 10, 31), "20260101T1030"), (datetime(2026, 1, 1, 0, 14), "20260101T0000")])
def test_every_minutes_slot_should_floor(now, expected):
    assert due_slot("EVERY_MINUTES", now, every_minutes=15) == expected
