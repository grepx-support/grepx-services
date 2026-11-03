# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SCORE — recompute a referrer's points on demand."""
from grepx_service import RequestContext

from .common import rescore


def handle(ctx: RequestContext) -> None:
    ctx.accept(rescore(ctx.emitter, ctx.read, ctx.text("person_id")))
