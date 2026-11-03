# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Task rules: who may change a task, and when a reminder is due. Pure."""
from __future__ import annotations

from datetime import datetime, timedelta

REMIND_HORIZON = timedelta(hours=24)
REMIND_COOLDOWN = timedelta(hours=12)


def can_edit(task: dict, actor_id: str, is_manager: bool) -> bool:
    return is_manager or actor_id in (task.get("created_by"), task.get("assignee_id"))


def reminder_due(task: dict, now: datetime) -> bool:
    if not task.get("remind") or task.get("state") == "done" or not task.get("due_at") or not task.get("assignee_id"):
        return False
    due = datetime.fromisoformat(task["due_at"]).replace(tzinfo=now.tzinfo)
    last = task.get("reminded_at")
    recent = last and now - datetime.fromisoformat(last).replace(tzinfo=now.tzinfo) < REMIND_COOLDOWN
    return due - now <= REMIND_HORIZON and not recent
