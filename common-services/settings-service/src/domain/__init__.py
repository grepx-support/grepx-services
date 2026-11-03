# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Setting names: letters, digits, dots, dashes and underscores (e.g. SMTP_HOST, auto.welcome.channels). Pure."""
import re

NAME = re.compile(r"^[A-Za-z0-9_.\-]{1,120}$")
MAX_VALUE = 20_000


def valid_name(name: str) -> bool:
    return bool(NAME.match(name or ""))


__all__ = ["valid_name", "MAX_VALUE"]
