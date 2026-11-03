"""Reacts to scheduler ticks (job task-reminders): remind assignees of tasks due within 24 h, at most every 12 h."""
from datetime import datetime

from grepx_service import Emitter, Reader, notify, now_iso, state_of
from grepx_service.wire import local_tz

from domain import reminder_due
from dto import TASKS_TABLE, TaskField as F

JOB = "task-reminders"


def handle_tick(app, row, cfg, now=None) -> int:
    if row.fields.get("job") != JOB or row.fields.get("status") != "NEW":
        return 0
    emitter, read, sent = Emitter(app, cfg, cause=row), Reader(app.client), 0
    now = now or datetime.now(local_tz())
    for task in read.accepted(TASKS_TABLE):
        if not reminder_due(task, now):
            continue
        channels = ["email", "sms", "whatsapp"] if task.get(F.IMPORTANT.value) else ["email", "whatsapp"]
        notify(emitter, "task_reminder", email=task.get(F.ASSIGNEE_EMAIL.value, ""), phone=task.get(F.ASSIGNEE_PHONE.value, ""),
               channels=channels, values={"first_name": (task.get(F.ASSIGNEE_NAME.value) or "").split(" ")[0],
                                          "title": task.get(F.TITLE.value), "due": task.get(F.DUE_AT.value, "").replace("T", " ")},
               ref=f"remind-{task['_key']}-{row.key}", tenant_id=task.get(F.TENANT_ID.value, ""), auto=False)
        fields = state_of(task)
        emitter.submit(TASKS_TABLE, task["_key"], "ACCEPTED", {**fields, F.REMINDED_AT.value: now.isoformat(timespec="minutes")})
        sent += 1
    emitter.submit("ticks", row.key, "ACCEPTED", {**row.fields, "processed_at": now_iso(), "count": sent})
    return sent
