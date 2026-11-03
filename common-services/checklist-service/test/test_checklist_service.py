"""checklist-service with the real task-service: apply twice = no duplicates; remove open only."""
from pathlib import Path

import pytest
from grepx_testkit.harness import ServiceHarness, load_service
from grepx_config import load_config

from routes import handle

HERE = Path(__file__).resolve().parents[1]
cfg = load_config(HERE / "config")
ITEMS = [{"phase": "Planning", "title": "Book venue", "days": -42, "important": True},
         {"phase": "Drive day", "title": "Set up", "days": 0, "time": "08:00"}]


@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, "checklist_requests", handle, cfg.live_criteria)
    task_handle, task_cfg, _ = load_service(HERE.parent / "task-service")
    harness.add(task_cfg, "task_requests", task_handle, task_cfg.live_criteria)
    harness.call("checklist_requests", "checklist-service", {"action": "SEED_TEMPLATE", "template_key": "drive", "items": ITEMS})
    return harness


def apply(h):
    return h.call("checklist_requests", "checklist-service", {"action": "APPLY", "template_key": "drive", "ref_type": "drive",
                                                              "ref_id": "d1", "base_date": "2026-03-01", "actor_id": "a"})


def test_apply_twice_should_not_duplicate(h):
    assert apply(h).fields["created"] == 2
    assert apply(h).fields["created"] == 0
    tasks = h.rows("tasks", status="ACCEPTED")
    assert sorted(t["due_at"] for t in tasks) == ["2026-01-18T09:00", "2026-03-01T08:00"]


def test_remove_only_open_should_keep_started_tasks(h):
    apply(h)
    started = [t for t in h.rows("tasks") if t["title"] == "Set up"][0]
    h.call("task_requests", "task-service", {"action": "CHANGE_STATUS", "task_id": started["_key"], "state": "in_progress", "actor_is_manager": True})
    v = h.call("checklist_requests", "checklist-service", {"action": "REMOVE", "template_key": "drive", "ref_id": "d1", "only_open": True})
    assert v.fields["removed"] == 1
    assert [t["title"] for t in h.rows("tasks", status="ACCEPTED")] == ["Set up"]


def test_unknown_template_should_reject(h):
    v = h.call("checklist_requests", "checklist-service", {"action": "APPLY", "template_key": "nope", "ref_id": "d", "base_date": "2026-01-01"})
    assert v.reason == "UNKNOWN_TEMPLATE"
