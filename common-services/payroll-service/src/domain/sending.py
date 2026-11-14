# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Sending a payslip to the person: only a locked month's payslip goes out, on channels the person can be reached on."""
from __future__ import annotations

CHANNELS = ("email", "whatsapp", "sms")


def reachable(channels: list[str], email: str, phone: str) -> list[str]:
    """The asked channels the person has an address for; ValueError when a channel is unknown or none is left."""
    asked = list(dict.fromkeys(channels or ["email"]))
    if any(c not in CHANNELS for c in asked):
        raise ValueError("INVALID_CHANNEL")
    usable = [c for c in asked if (email if c == "email" else phone)]
    if not usable:
        raise ValueError("NO_CONTACT")
    return usable


def can_send(run: dict | None) -> str:
    """'' when the month's payslips may go out, else the reason."""
    if run is None:
        return "NO_RUN"
    return "" if run.get("final") else "MONTH_NOT_FINAL"
