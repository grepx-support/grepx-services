# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""REMOVE — delete a target's checklist tasks (all, or only those still To do); extra tasks are kept."""
from grepx_service import RequestContext, new_key

from dto import TASK_REQUESTS, TASK_SERVICE, TASKS_TABLE, ChecklistField as F


def handle(ctx: RequestContext) -> None:
    tasks = ctx.read.accepted(TASKS_TABLE, ref_id=ctx.text(F.REF_ID), checklist=ctx.text(F.TEMPLATE_KEY))
    if ctx.get(F.ONLY_OPEN, False):
        tasks = [t for t in tasks if t.get("state") == "todo"]
    for t in tasks:
        ctx.request(TASK_REQUESTS, new_key(), {"action": "DELETE", "task_id": t["_key"], "actor_id": ctx.text(F.ACTOR_ID),
                                               "actor_is_manager": True}, TASK_SERVICE)
    ctx.accept({F.REMOVED: len(tasks)})
