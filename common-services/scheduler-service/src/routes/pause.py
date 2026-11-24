# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""PAUSE / RESUME - a paused schedule does not fire; resumed, it fires from the next time on (none of the ones missed)."""
from grepx_service import RequestContext

from dto import ScheduleField as F
from . import common
from .common import changed


def pause(ctx: RequestContext) -> None:
    changed(ctx, lambda s: {**s, F.PAUSED.value: True})


def resume(ctx: RequestContext) -> None:
    changed(ctx, lambda s: {**s, F.PAUSED.value: False, F.SINCE.value: common.CLOCK().isoformat()})
