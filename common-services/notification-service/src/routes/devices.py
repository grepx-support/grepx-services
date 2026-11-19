# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""REGISTER_DEVICE / FORGET_DEVICE (a person's Web Push subscriptions), PUSH_KEY (the VAPID public key, the pair made the
first time it is asked for), MARK_SEEN (the bell opened). Devices are kept per person, any number."""
from __future__ import annotations

import base64
import hashlib

from grepx_service import RequestContext, now_iso

from dto import DEVICES_TABLE, KEYS_TABLE, SEEN_TABLE, ReasonCode

PAIR = "vapid"


def _user(ctx: RequestContext) -> str:
    return ctx.text("user_id")


def device_key(endpoint: str) -> str:
    return hashlib.sha1(endpoint.encode()).hexdigest()


def register(ctx: RequestContext) -> None:
    sub = ctx.get("subscription") or {}
    if not _user(ctx):
        return ctx.reject(ReasonCode.MISSING_USER)
    if not isinstance(sub, dict) or not str(sub.get("endpoint", "")).startswith("https://") or not (sub.get("keys") or {}).get("p256dh"):
        return ctx.reject(ReasonCode.BAD_SUBSCRIPTION)
    key = device_key(sub["endpoint"])
    ctx.emitter.submit(DEVICES_TABLE, key, "ACCEPTED", {"user_id": _user(ctx), "tenant_id": ctx.text("tenant_id"), "subscription": sub,
                                                        "label": ctx.text("label")[:80], "added_at": now_iso(), "active": True})
    ctx.accept({"device": key})


def forget(ctx: RequestContext) -> None:
    key = device_key(ctx.text("endpoint")) if ctx.text("endpoint") else ctx.text("device")
    row = ctx.read.accepted_one(DEVICES_TABLE, key)
    if row and row.get("user_id") == _user(ctx):
        ctx.emitter.submit(DEVICES_TABLE, key, "ACCEPTED", {**{k: v for k, v in row.items() if not k.startswith("_") and k != "status"}, "active": False})
    ctx.accept({"forgotten": bool(row)})


def make_pair() -> dict:
    from cryptography.hazmat.primitives import serialization  # noqa: PLC0415
    from cryptography.hazmat.primitives.asymmetric import ec  # noqa: PLC0415
    private = ec.generate_private_key(ec.SECP256R1())
    raw = private.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    pem = private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
    return {"public": base64.urlsafe_b64encode(raw).decode().rstrip("="), "private": pem}


def pair(ctx: RequestContext) -> dict:
    return ctx.read.accepted_one(KEYS_TABLE, PAIR) or {}


def push_key(ctx: RequestContext) -> None:
    got = pair(ctx)
    if not got.get("public"):
        got = make_pair()
        ctx.emitter.submit(KEYS_TABLE, PAIR, "ACCEPTED", got)
    ctx.accept({"public_key": got["public"]})


def mark_seen(ctx: RequestContext) -> None:
    if not _user(ctx):
        return ctx.reject(ReasonCode.MISSING_USER)
    at = now_iso()
    ctx.emitter.submit(SEEN_TABLE, _user(ctx), "ACCEPTED", {"seen_until": at})
    ctx.accept({"seen_until": at})


def devices_of(ctx: RequestContext, user_id: str) -> list[dict]:
    return [d for d in ctx.read.accepted(DEVICES_TABLE, user_id=user_id) if d.get("active", True)]


def vapid(ctx: RequestContext) -> dict | None:
    p = pair(ctx)
    if not p.get("private"):
        return None
    import os  # noqa: PLC0415
    return {**p, "subject": os.environ.get("VAPID_SUBJECT", "")}
