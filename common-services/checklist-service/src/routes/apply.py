"""APPLY — create the template's missing tasks for one target (idempotent by title)."""
from grepx_service import RequestContext

from domain import due_at, stable_id
from dto import ASSIGNEE_FIELDS, TASK_REQUESTS, TASK_SERVICE, TASKS_TABLE, TEMPLATES_TABLE, ChecklistField as F, ReasonCode


def handle(ctx: RequestContext) -> None:
    template = ctx.read.accepted_one(TEMPLATES_TABLE, ctx.text(F.TEMPLATE_KEY))
    if template is None:
        return ctx.reject(ReasonCode.UNKNOWN_TEMPLATE)
    ref_id, base = ctx.text(F.REF_ID), ctx.text(F.BASE_DATE)
    if not ref_id or not base:
        return ctx.reject(ReasonCode.MISSING_FIELD)
    have = {t.get("title") for t in ctx.read.accepted(TASKS_TABLE, ref_id=ref_id)}
    created = 0
    for item in template[F.ITEMS.value]:
        if item["title"] in have:
            continue
        task_id = stable_id(ref_id, item["title"])
        ctx.request(TASK_REQUESTS, stable_id(task_id, "create"), {
            "action": "CREATE", "task_id": task_id, "title": item["title"], "description": item.get("details", ""),
            "due_at": due_at(base, item.get("days", 0), item.get("time", "09:00")), "important": bool(item.get("important")),
            "remind": True, "phase": item.get("phase", ""), "checklist": template[F.TEMPLATE_KEY.value],
            "ref_type": ctx.text(F.REF_TYPE), "ref_id": ref_id, "ref_label": ctx.text(F.REF_LABEL),
            "actor_id": ctx.text(F.ACTOR_ID), "tenant_id": ctx.text(F.TENANT_ID), **{f: ctx.text(f) for f in ASSIGNEE_FIELDS}}, TASK_SERVICE)
        created += 1
    ctx.accept({F.CREATED: created})
