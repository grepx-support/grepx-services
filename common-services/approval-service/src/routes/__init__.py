# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for approval-service: ASK, DECIDE, WITHDRAW. Who may decide comes from the business's staff roles
(access-service): any role holding one of the approval's perms. Approvers and the asker are emailed through
notification-service (templates approval_request, approval_decided - in the product's words)."""
from __future__ import annotations

import grepx_contracts as gc
from grepx_service import ActionDispatcher, RequestContext, new_key, notify, now_iso

from domain import clean_ask, may_decide, outgoing
from dto import APPROVALS, ApprovalAction as A, ApprovalState as S, ReasonCode as R


class Stop(Exception):
    pass


def role_perms(ctx: RequestContext, user_id: str) -> set[str]:
    acc = ctx.read.accepted_one(gc.access.USER_ACCESS, user_id) if user_id else None
    role = ctx.read.accepted_one(gc.access.STAFF_ROLES, acc["staff_role_id"]) if acc and acc.get("staff_role_id") else None
    return set((role or {}).get("perms") or [])


def deciders(ctx: RequestContext, tenant: str, perms: list[str]) -> list[dict]:
    """People of this business whose staff role holds one of perms, with their contact details."""
    roles = {r["_key"]: set(r.get("perms") or []) for r in ctx.read.accepted(gc.access.STAFF_ROLES) if r["_key"].startswith(f"{tenant}.")}
    out = []
    for a in ctx.read.accepted(gc.access.USER_ACCESS):
        if may_decide(roles.get(a.get("staff_role_id", ""), set()), perms):
            person = ctx.read.accepted_one(gc.people.PEOPLE, a["_key"]) or {}
            out.append({"user_id": a["_key"], "name": person.get("name", ""), "email": person.get("email", ""), "phone": person.get("phone", "")})
    return out


def money(row: dict) -> str:
    return f"{row.get('currency', '')} {row['amount'] / 100:,.2f}".strip() if row.get("amount") is not None else ""


def tell(ctx: RequestContext, template: str, person: dict, row: dict, ref: str, **values) -> None:
    notify(ctx.emitter, template, email=person.get("email", ""), channels=["email"], ref=ref, tenant_id=row["tenant_id"], user_id=person.get("user_id", ""),
           values={"first_name": (person.get("name") or "").split(" ")[0], "title": row["title"], "by": row["by_name"], "amount": money(row),
                   "details": "\n".join(f"- {d['k']}: {d['v']}" for d in row.get("details") or []), "link": row.get("link", ""), **values})


def mine(ctx: RequestContext, tenant: str) -> dict:
    row = ctx.read.accepted_one(APPROVALS, ctx.text("approval_id"))
    if row is None or row.get("tenant_id") != tenant:
        raise Stop(R.UNKNOWN_APPROVAL)
    return {k: v for k, v in row.items() if not k.startswith("_") and k != "status"} | {"approval_id": row["_key"]}


def run(ctx: RequestContext, body) -> None:
    tenant = ctx.text("tenant_id")
    if not tenant:
        return ctx.reject(R.MISSING_TENANT)
    try:
        out = body(tenant)
    except Stop as stop:
        return ctx.reject(stop.args[0])
    except ValueError as exc:
        return ctx.reject(str(exc))
    ctx.accept(out)


def ask(ctx: RequestContext) -> None:
    def body(tenant):
        a = clean_ask({k: ctx.get(k) for k in ("kind", "title", "ref", "amount", "currency", "details", "link", "perms", "then", "otherwise")})
        who = deciders(ctx, tenant, a["perms"])
        if not who:
            raise Stop(R.NO_DECIDERS)
        same = next((r for r in ctx.read.accepted(APPROVALS, tenant_id=tenant, state=S.PENDING.value, kind=a["kind"], ref=a["ref"])), None) if a["ref"] else None
        key = same["_key"] if same else new_key()[:16]
        row = {"approval_id": key, "tenant_id": tenant, **a, "state": S.PENDING.value, "at": now_iso(), "by": ctx.text("actor_id"),
               "by_name": ctx.text("actor_name"), "by_email": (ctx.read.accepted_one(gc.people.PEOPLE, ctx.text("actor_id")) or {}).get("email", "")}
        ctx.emitter.submit(APPROVALS, key, "ACCEPTED", row)
        others = [p for p in who if p["user_id"] != row["by"]]
        for person in others:
            tell(ctx, "approval_request", person, row, f"appr-{key}")
        return {"approval": row, "told": len(others)}
    run(ctx, body)


def decide(ctx: RequestContext) -> None:
    def body(tenant):
        row = mine(ctx, tenant)
        if row["state"] != S.PENDING.value:
            raise Stop(R.ALREADY_DECIDED)
        me, yes, note = ctx.text("actor_id"), bool(ctx.get("approve")), ctx.text("note")[:300]
        if not may_decide(role_perms(ctx, me), row["perms"]):
            raise Stop(R.NOT_ALLOWED)
        if me == row["by"] and any(p["user_id"] != me for p in deciders(ctx, tenant, row["perms"])):
            raise Stop(R.OWN_REQUEST)                  # four eyes - unless nobody else could ever decide it
        if not yes and not note:
            raise Stop(R.NOTE_REQUIRED)
        row.update({"state": (S.APPROVED if yes else S.REJECTED).value, "decided_at": now_iso(), "decided_by": me,
                    "decided_by_name": ctx.text("actor_name"), "note": note})
        request = row["then"] if yes else row["otherwise"]
        if request:
            ctx.request(request["table"], f"appr-{row['approval_id']}", outgoing(request, row, note), request["service"])
            row["sent"] = True
        ctx.emitter.submit(APPROVALS, row["approval_id"], "ACCEPTED", row)
        if row.get("by_email") and row["by"] != me:
            tell(ctx, "approval_decided", {"email": row["by_email"], "name": row["by_name"], "user_id": row["by"]}, row, f"appr-done-{row['approval_id']}",
                 decision="approved" if yes else "not approved", decided_by=row["decided_by_name"], note=note)
        return {"approval": row}
    run(ctx, body)


def withdraw(ctx: RequestContext) -> None:
    def body(tenant):
        row = mine(ctx, tenant)
        if row["state"] != S.PENDING.value:
            raise Stop(R.ALREADY_DECIDED)
        if row["by"] != ctx.text("actor_id"):
            raise Stop(R.NOT_YOURS)
        row.update({"state": S.WITHDRAWN.value, "decided_at": now_iso()})
        ctx.emitter.submit(APPROVALS, row["approval_id"], "ACCEPTED", row)
        return {"approval": row}
    run(ctx, body)


handle = ActionDispatcher({A.ASK: ask, A.DECIDE: decide, A.WITHDRAW: withdraw}, A, "approval_requests")
