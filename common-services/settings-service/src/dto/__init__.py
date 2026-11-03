"""Single import door for settings-service vocabulary."""
from .settings_action import SettingsAction

SETTINGS_TABLE = "app_settings"

__all__ = ["SettingsAction", "SETTINGS_TABLE"]
