# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""RECORD — keep an audit entry (written by grepx_audit.write_audit from any service)."""
from grepx_service import RequestContext


def handle(ctx: RequestContext) -> None:
    if not ctx.text("action") or not ctx.text("entity_type"):
        return ctx.reject("MISSING_FIELD")
    ctx.accept()
