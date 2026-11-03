# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""CHECK — evaluate the quick form with the product's rules. Nothing about the person is stored beyond this request row."""
from grepx_service import RequestContext

from dto import INVALID_ANSWERS, NOT_CONFIGURED, QuestionnaireField as F
from .rules import rules


def handle(ctx: RequestContext) -> None:
    product = rules(ctx)
    if product is None:
        return ctx.reject(NOT_CONFIGURED)
    try:
        ok, reasons, notes = product.check(dict(ctx.get(F.ANSWERS, {})))
    except ValueError:
        return ctx.reject(INVALID_ANSWERS)
    ctx.accept({F.ANSWERS: {}, F.ELIGIBLE: ok, F.REASONS: reasons, F.NOTES: notes})
