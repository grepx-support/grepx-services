# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""task-service: create/update/status/claim/delete, edit policy, assignment notice, reminders."""
from datetime import datetime
from pathlib import Path

import pytest
from grepx_testkit.harness import ServiceHarness
from nexus_api import NexusApplication, Row
from grepx_config import load_config
from nexus_testkit import MemoryClient

from domain import reminder_due
from jobs.reminders import handle_tick
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")


@pytest.fixture()
def h():
    return ServiceHarness().add(cfg, "task_requests", handle, cfg.live_criteria)


def call(h, **f):
    return h.call("task_requests", "task-service", {"actor_id": "u1", **f})


def task(h, key):
    return h.read.accepted_one("tasks", key)


def test_create_should_project_task_and_notify_other_assignee(h):
    v = call(h, action="CREATE", title="Book venue", assignee_id="u2", assignee_email="b@x.sg", important=True)
    t = task(h, v.fields["task_id"])
    assert t["state"] == "todo" and t["events"][0]["action"] == "created"
    assert h.rows("notifications")[0]["template"] == "task_assigned"


def test_stranger_cannot_change_status(h):
    tid = call(h, action="CREATE", title="x").fields["task_id"]
    assert call(h, action="CHANGE_STATUS", task_id=tid, state="done", actor_id="intruder").reason == "NOT_ALLOWED"
    assert call(h, action="CHANGE_STATUS", task_id=tid, state="done", actor_id="boss", actor_is_manager=True).ok


def test_invalid_state_should_reject(h):
    tid = call(h, action="CREATE", title="x").fields["task_id"]
    assert call(h, action="CHANGE_STATUS", task_id=tid, state="flying").reason == "INVALID_STATE"


def test_claim_should_only_take_unassigned(h):
    tid = call(h, action="CREATE", title="x").fields["task_id"]
    assert call(h, action="CLAIM", task_id=tid, actor_id="u3").ok
    assert call(h, action="CLAIM", task_id=tid, actor_id="u4").reason == "ALREADY_ASSIGNED"


def test_delete_should_hide_task(h):
    tid = call(h, action="CREATE", title="x").fields["task_id"]
    assert call(h, action="DELETE", task_id=tid).ok and task(h, tid) is None


def test_reminder_rules():
    now = datetime(2026, 1, 1, 9, 0)
    base = {"remind": 1, "assignee_id": "u", "due_at": "2026-01-01T20:00", "state": "todo"}
    assert reminder_due(base, now)
    assert not reminder_due({**base, "due_at": "2026-01-03T20:00"}, now)
    assert not reminder_due({**base, "reminded_at": "2026-01-01T03:00"}, now)
    assert not reminder_due({**base, "state": "done"}, now)


def test_tick_should_remind_once(h):
    tid = call(h, action="CREATE", title="x", assignee_id="u2", assignee_email="b@x.sg", remind=1, due_at="2026-01-01T20:00").fields["task_id"]
    app = NexusApplication(MemoryClient(h.engine), "ticks")
    tick = Row("t1", {"status": "NEW", "job": "task-reminders"})
    assert handle_tick(app, tick, cfg, now=datetime(2026, 1, 1, 9, 0)) == 1
    assert handle_tick(app, Row("t2", {"status": "NEW", "job": "task-reminders"}), cfg, now=datetime(2026, 1, 1, 10, 0)) == 0
    assert task(h, tid)["reminded_at"].startswith("2026-01-01T09")
