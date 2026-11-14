# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""ATTACH - keep a staged file as it is (a PDF, photo, spreadsheet ...) attached to a record: ref says which ("bill:123",
"supplier:abc"); listed by owner and ref. Only document and picture types are kept."""
from grepx_service import RequestContext, now_iso

from dto import MEDIA_TABLE, MediaField as F, MediaKind
from files import kind_of, safe_name
from .common import Deps


def handle(ctx: RequestContext) -> None:
    store = Deps.store()
    staged = ctx.text(F.STAGED_KEY)
    data = store.get(staged)
    try:
        mime, ext = kind_of(data or b"", ctx.text(F.NAME))
    except ValueError as exc:
        if data:
            store.delete(staged)
        return ctx.reject(str(exc))
    media_id = ctx.text(F.MEDIA_ID) or ctx.key
    key = f"file/{media_id[:2]}/{media_id}.{ext}"
    store.put(key, data, mime)
    store.delete(staged)
    info = {F.MEDIA_ID.value: media_id, F.KIND.value: MediaKind.FILE.value, F.KEY.value: key, F.CONTENT_TYPE.value: mime, F.SIZE.value: len(data),
            F.OWNER_ID.value: ctx.text(F.OWNER_ID), F.REF.value: ctx.text(F.REF)[:80], F.NAME.value: safe_name(ctx.text(F.NAME)),
            F.NOTE.value: ctx.text(F.NOTE)[:200], F.BY.value: ctx.text(F.BY)[:80], F.AT.value: now_iso()}
    ctx.emitter.submit(MEDIA_TABLE, media_id, "ACCEPTED", info)
    ctx.accept(info)
