# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Single import door for template-service vocabulary."""
from .reason_code import ReasonCode
from .template_action import TemplateAction
from .template_field import TemplateField

TEMPLATES_TABLE = "message_templates"
SETTINGS_TABLE = "message_settings"
CHANNELS = ("email", "sms", "whatsapp")

__all__ = ["ReasonCode", "TemplateAction", "TemplateField", "TEMPLATES_TABLE", "SETTINGS_TABLE", "CHANNELS"]
