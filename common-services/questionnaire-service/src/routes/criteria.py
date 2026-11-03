"""CRITERIA — the product's requirements as data, so websites and apps show the same numbers the rules use."""
from grepx_service import RequestContext

from dto import NOT_CONFIGURED, QuestionnaireField as F
from .rules import rules


def handle(ctx: RequestContext) -> None:
    product = rules(ctx)
    if product is None:
        return ctx.reject(NOT_CONFIGURED)
    ctx.accept({F.CRITERIA: product.criteria()})
