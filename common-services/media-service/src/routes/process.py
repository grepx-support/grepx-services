# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""PROCESS — turn a staged upload into a stored image (WebP, or PNG for a logo) and publish it in `media`."""
from grepx_service import RequestContext

from dto import MEDIA_TABLE, MediaField as F, MediaKind, ReasonCode
from processing import PROFILES, ImageError, process
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
        image, width, height = process(data, kind)
    except ImageError as exc:
        store.delete(ctx.text(F.STAGED_KEY))
        return ctx.reject(str(exc))
    media_id = ctx.text(F.MEDIA_ID) or ctx.key
    profile = PROFILES[kind]
    key = f"{kind}/{media_id[:2]}/{media_id}.{profile.ext}"
    store.put(key, image, profile.mime)
    store.delete(ctx.text(F.STAGED_KEY))
    info = {F.MEDIA_ID.value: media_id, F.KIND.value: kind, F.KEY.value: key, F.CONTENT_TYPE.value: profile.mime,
            F.SIZE.value: len(image), F.WIDTH.value: width, F.HEIGHT.value: height, F.OWNER_ID.value: ctx.text(F.OWNER_ID)}
    ctx.emitter.submit(MEDIA_TABLE, media_id, "ACCEPTED", info)
    ctx.accept(info)
