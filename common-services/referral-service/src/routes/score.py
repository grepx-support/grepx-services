"""SCORE — recompute a referrer's points on demand."""
from grepx_service import RequestContext

from .common import rescore


def handle(ctx: RequestContext) -> None:
    ctx.accept(rescore(ctx.emitter, ctx.read, ctx.text("person_id")))
