"""DELETE — remove a setting (readers fall back to the default / .env value)."""
from grepx_service import RequestContext

from dto import SETTINGS_TABLE


def handle(ctx: RequestContext) -> None:
    name = ctx.text("name")
    if ctx.read.accepted_one(SETTINGS_TABLE, name):
        ctx.emitter.submit(SETTINGS_TABLE, name, "DELETED", {"name": name})
    ctx.accept({"name": name})
