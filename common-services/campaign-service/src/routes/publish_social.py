"""PUBLISH_SOCIAL — post an event (caption, poster image, link) to the chosen networks: Facebook Page, Instagram,
LinkedIn page, X, Telegram channel. Every attempt is recorded in social_posts with the network's answer."""
import grepx_contracts as gc
from grepx_service import RequestContext, new_key, now_iso

from social import SOCIAL
from social import settings as social_settings
from social.channels import Post
from social.graph import GraphError

POSTS_TABLE = "social_posts"


def _image(url: str) -> bytes:
    if not url:
        return b""
    try:
        import requests
        r = requests.get(url, timeout=20)
        return r.content if r.ok else b""
    except Exception:
        return b""


def handle(ctx: RequestContext) -> None:
    event_id, caption = ctx.text("event_id"), ctx.text("caption")
    networks = [n for n in ctx.get("networks", []) if n in SOCIAL]
    if not event_id or not networks:
        return ctx.reject("NOTHING_TO_PUBLISH")
    social_settings.load(ctx.read.accepted(gc.settings.APP_SETTINGS))
    image_url, link = ctx.text("image_url"), ctx.text("link")
    image = _image(image_url)
    results = {}
    for key in networks:
        ch = SOCIAL[key]
        row = {"event_id": event_id, "network": key, "caption": caption, "created_by": ctx.text("actor_id"), "created": now_iso(),
               "external_id": "", "permalink": "", "error": ""}
        if not ch.configured():
            row.update(post_status="failed", error=f"{ch.label} is not set up ({ch.setup_hint}).")
        else:
            try:
                r = ch.publish(Post(caption, image_url, link, image))
                row.update(post_status="posted", external_id=r.external_id or "", permalink=r.permalink or "")
            except (GraphError, KeyError, ValueError) as e:
                row.update(post_status="failed", error=str(e)[:500])
        post_id = new_key()
        ctx.emitter.submit(POSTS_TABLE, post_id, "ACCEPTED", {"post_id": post_id, **row})
        results[key] = {"ok": row["post_status"] == "posted", "info": row["permalink"] or row["error"]}
    ctx.accept({"results": results})
