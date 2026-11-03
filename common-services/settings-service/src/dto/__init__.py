# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Single import door for settings-service vocabulary."""
from .settings_action import SettingsAction

SETTINGS_TABLE = "app_settings"

__all__ = ["SettingsAction", "SETTINGS_TABLE"]
