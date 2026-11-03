# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Custom wording may only use the placeholders the template declares."""
import re

PATTERN = re.compile(r"\{(\w+)\}")


def placeholders_in(*texts: str) -> set[str]:
    return {m for t in texts for m in PATTERN.findall(t or "")}
