# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The product's questionnaire rules (config plugins.questionnaire); None when the deployment has none."""
from grepx_service import RequestContext
from grepx_service.plugins import plugin


def rules(ctx: RequestContext):
    return plugin(ctx.cfg, "questionnaire")
