# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

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


# --- cron rules, pause / resume, run now, preview, listing, tick history, health ----------------------------------------
from datetime import timezone as _tz  # noqa: E402

import routes.common as common  # noqa: E402

UTC = _tz.utc


def at(*a):
    return datetime(*a, tzinfo=UTC)


def cron(h, sid="c1", line="20 0 * * *", tz="UTC", **f):
    return h.call("schedule_requests", "scheduler-service", {"action": "REGISTER", "schedule_id": sid, "job": "sea-run", "target_service": "x-service",
                                                              "kind": "CRON", "cron": line, "timezone": tz, "tenant_id": "gx", "owner": "sea:s1",
                                                              "label": "Crypto · daily data", "payload": '{"job": "crypto_daily"}', **f})


def act(h, action, **f):
    return h.call("schedule_requests", "scheduler-service", {"action": action, "tenant_id": "gx", **f})


def ticker(h, when):
    return Ticker(NexusApplication(MemoryClient(h.engine), "ticks"), cfg, clock=lambda: when)


def test_a_cron_schedule_fires_once_per_time_never_for_times_before_it_was_made(h, monkeypatch):
    monkeypatch.setattr(common, "CLOCK", lambda: at(2026, 1, 5, 0, 30))
    made = cron(h)
    assert made.ok, made.reason
    s = made.fields["schedule"]
    assert s["words"] == "every day at 00:20 UTC" and s["next_runs"].split(",")[0] == "2026-01-06T00:20:00+00:00"
    assert ticker(h, at(2026, 1, 5, 23, 0)).tick() == 0                 # 00:20 today was before it was made
    assert ticker(h, at(2026, 1, 6, 0, 25)).tick() == 1 and ticker(h, at(2026, 1, 6, 0, 40)).tick() == 0
    tick = h.rows("ticks")[0]
    assert tick["slot"] == "20260106T0020" and tick["to_service"] == "x-service" and tick["payload"] == '{"job": "crypto_daily"}'
    assert tick["tenant_id"] == "gx" and tick["label"] == "Crypto · daily data"
    kept = h.read.accepted_one("schedules", "c1")
    assert kept["last_fired"] == "20260106T0020" and kept["next_runs"].startswith("2026-01-07T00:20")


def test_cron_in_a_timezone_and_bad_rules_refused(h, monkeypatch):
    monkeypatch.setattr(common, "CLOCK", lambda: at(2026, 1, 5, 0, 0))
    sg = cron(h, sid="sg", line="0 9 * * 1-5", tz="Asia/Singapore").fields["schedule"]
    assert sg["words"] == "weekdays at 09:00 Asia/Singapore" and sg["next_runs"].split(",")[0] == "2026-01-05T09:00:00+08:00"
    assert cron(h, sid="bad", line="61 * * * *").reason == "INVALID_SCHEDULE"
    assert cron(h, sid="bad", tz="Mars/Base").reason == "INVALID_TIMEZONE"
    p = act(h, "PREVIEW", kind="CRON", cron="0 */6 * * *", timezone="UTC")
    assert p.ok and p.fields["words"] == "every 6 hours at :00 (UTC)" and len(p.fields["next_runs"]) == 5
    assert act(h, "PREVIEW", kind="CRON", cron="nope").reason == "INVALID_SCHEDULE"


def test_paused_does_not_fire_resumed_fires_from_then_and_run_now_ticks_at_once(h, monkeypatch):
    monkeypatch.setattr(common, "CLOCK", lambda: at(2026, 1, 5, 0, 0))
    cron(h, line="0 * * * *")
    assert act(h, "PAUSE", schedule_id="c1").fields["schedule"]["paused"] is True
    assert ticker(h, at(2026, 1, 5, 3, 5)).tick() == 0
    monkeypatch.setattr(common, "CLOCK", lambda: at(2026, 1, 5, 3, 10))
    resumed = act(h, "RESUME", schedule_id="c1").fields["schedule"]
    assert resumed["paused"] is False and resumed["next_runs"].startswith("2026-01-05T04:00")
    assert ticker(h, at(2026, 1, 5, 3, 30)).tick() == 0                  # 03:00 was missed while paused - not fired late
    assert ticker(h, at(2026, 1, 5, 4, 1)).tick() == 1
    now = act(h, "RUN_NOW", schedule_id="c1")
    assert now.ok and h.read.one("ticks", now.fields["tick"])["manual"] is True
    assert act(h, "PAUSE", schedule_id="nope").reason == "UNKNOWN_SCHEDULE"
    assert act(h, "PAUSE", schedule_id="c1", tenant_id="other").reason == "UNKNOWN_SCHEDULE"      # another organisation's


def test_listing_tick_history_and_health(h, monkeypatch):
    monkeypatch.setattr(common, "CLOCK", lambda: at(2026, 1, 5, 0, 0))
    cron(h, sid="a", line="0 * * * *")
    cron(h, sid="b", line="30 * * * *", owner="sea:s2")
    assert [s["schedule_id"] for s in act(h, "SCHEDULES").fields["schedules"]] == ["a", "b"]
    assert [s["schedule_id"] for s in act(h, "SCHEDULES", owner="sea:s2").fields["schedules"]] == ["b"]
    assert act(h, "HEALTH").fields["alive"] is False
    ticker(h, at(2026, 1, 5, 1, 1)).tick()
    ticker(h, at(2026, 1, 5, 2, 1)).tick()
    history = act(h, "TICKS", schedule_id="a").fields["ticks"]
    assert [t["slot"] for t in history] == ["20260105T0200", "20260105T0100"] and history[0]["status"] == "NEW"
    monkeypatch.setattr(common, "CLOCK", lambda: at(2026, 1, 5, 2, 2))
    assert act(h, "HEALTH").fields["alive"] is True


@pytest.mark.parametrize("line,first", [("0 9 * * 1-5", "2026-01-05T09:00"), ("0 9 * * 0", "2026-01-11T09:00"), ("0 9 * * 7", "2026-01-11T09:00"),
                                        ("0 9 * * 6", "2026-01-10T09:00"), ("0 9 1 * *", "2026-02-01T09:00")])
def test_weekdays_count_from_sunday_as_in_cron(line, first):
    from domain.rules import Cron
    assert Cron(line, "UTC").upcoming(at(2026, 1, 5, 0, 0), 1)[0].isoformat().startswith(first)
