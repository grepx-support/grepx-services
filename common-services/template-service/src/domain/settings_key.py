# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Where the settings of one automatic message are kept: the platform default under the template's key, one business's
own choice under "<tenant>:<template>" (notification-service looks for the business's first)."""


def settings_key(template: str, tenant: str = "") -> str:
    return f"{tenant}:{template}" if tenant else template
