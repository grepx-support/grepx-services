# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""CHAT — one chat turn of the product's question flow. The caller keeps the conversation state and sends it back each turn."""
from grepx_service import RequestContext

from dto import NOT_CONFIGURED, QuestionnaireField as F
from .rules import rules


def handle(ctx: RequestContext) -> None:
    product = rules(ctx)
    if product is None:
        return ctx.reject(NOT_CONFIGURED)
    state = dict(ctx.get(F.STATE, {}))
    message = ctx.text(F.MESSAGE)
    if message.lower() in ("start over", "restart", ""):
        message = "__start__"
    reply = product.chat(state, message)
    ctx.accept({F.REPLY: reply, F.STATE: state})
