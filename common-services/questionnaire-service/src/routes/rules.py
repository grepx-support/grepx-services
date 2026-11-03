"""The product's questionnaire rules (config plugins.questionnaire); None when the deployment has none."""
from grepx_service import RequestContext
from grepx_service.plugins import plugin


def rules(ctx: RequestContext):
    return plugin(ctx.cfg, "questionnaire")
