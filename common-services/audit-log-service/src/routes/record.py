"""RECORD — keep an audit entry (written by grepx_audit.write_audit from any service)."""
from grepx_service import RequestContext


def handle(ctx: RequestContext) -> None:
    if not ctx.text("action") or not ctx.text("entity_type"):
        return ctx.reject("MISSING_FIELD")
    ctx.accept()
