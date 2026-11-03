"""PROCESS — turn a staged upload into a stored WebP image and publish it in `media`."""
from grepx_service import RequestContext

from dto import MEDIA_TABLE, MediaField as F, MediaKind, ReasonCode
from processing import ImageError, process
from .common import Deps


def handle(ctx: RequestContext) -> None:
    kind = ctx.text(F.KIND) or MediaKind.PICTURE.value
    if kind not in {k.value for k in MediaKind}:
        return ctx.reject(ReasonCode.UNKNOWN_KIND)
    store = Deps.store()
    data = store.get(ctx.text(F.STAGED_KEY))
    if not data:
        return ctx.reject(ReasonCode.MISSING_FILE)
    try:
        webp, width, height = process(data, kind)
    except ImageError as exc:
        store.delete(ctx.text(F.STAGED_KEY))
        return ctx.reject(str(exc))
    media_id = ctx.text(F.MEDIA_ID) or ctx.key
    key = f"{kind}/{media_id[:2]}/{media_id}.webp"
    store.put(key, webp, "image/webp")
    store.delete(ctx.text(F.STAGED_KEY))
    info = {F.MEDIA_ID.value: media_id, F.KIND.value: kind, F.KEY.value: key, F.CONTENT_TYPE.value: "image/webp",
            F.SIZE.value: len(webp), F.WIDTH.value: width, F.HEIGHT.value: height, F.OWNER_ID.value: ctx.text(F.OWNER_ID)}
    ctx.emitter.submit(MEDIA_TABLE, media_id, "ACCEPTED", info)
    ctx.accept(info)
