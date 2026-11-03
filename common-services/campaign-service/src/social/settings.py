# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Credentials for the social networks: what admins saved on the Integrations page (settings-service, secrets sealed
with the platform key), falling back to the environment. Loaded once per request by the PUBLISH_SOCIAL handler."""
from __future__ import annotations

import os

CURRENT: dict = {}


def load(rows: list[dict]) -> None:
    from grepx_auth import open_settings
    CURRENT.clear()
    CURRENT.update(open_settings(rows))

def setting(key: str, default: str = "") -> str:
    return CURRENT.get(key) or os.environ.get(key, default) or default
