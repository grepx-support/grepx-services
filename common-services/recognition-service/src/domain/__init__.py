# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Voucher allocation: one shared code for everyone, or unique codes handed out in order. Pure."""
import hashlib


class AllocationError(ValueError):
    pass


def certificate_code(person_id: str, event_id: str) -> str:
    return hashlib.sha256(f"cert|{person_id}|{event_id}".encode()).hexdigest()[:32]


def allocate(offer: dict, person_ids: list[str]) -> dict[str, str]:
    codes = [c.strip() for c in offer.get("codes") or [] if str(c).strip()]
    if codes:                     # unique codes go out in order until they run out (the rest are reported as short)
        return dict(zip(person_ids, codes))
    return {d: str(offer.get("code") or "") for d in person_ids}


__all__ = ["AllocationError", "certificate_code", "allocate"]
