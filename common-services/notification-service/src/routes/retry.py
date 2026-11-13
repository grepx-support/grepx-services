# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""RETRY - try one failed send again now (instead of waiting for the next automatic try). Only a business's own sends."""
from grepx_service import RequestContext

from domain import retry
from dto import Delivery, NotificationField as F, ReasonCode

TABLE = "notifications"
SERVICE = "notification-service"


def handle(ctx: RequestContext) -> None:
    row = ctx.read.accepted_one(TABLE, ctx.text(F.KEY))
    if row is None or (ctx.text(F.TENANT_ID) and row.get(F.TENANT_ID.value) != ctx.text(F.TENANT_ID)):
        return ctx.reject(ReasonCode.NOT_FAILED)
    if row.get(F.DELIVERY.value) != Delivery.FAILED.value:
        return ctx.reject(ReasonCode.NOT_FAILED)
    key = retry.next_key(row)
    if ctx.read.one(TABLE, key) is not None:
        return ctx.reject(ReasonCode.ALREADY_RETRIED)
    ctx.emitter.request(TABLE, key, retry.again(row), SERVICE)
    ctx.accept({F.KEY: key})
