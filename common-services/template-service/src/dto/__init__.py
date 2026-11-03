"""Single import door for template-service vocabulary."""
from .reason_code import ReasonCode
from .template_action import TemplateAction
from .template_field import TemplateField

TEMPLATES_TABLE = "message_templates"
SETTINGS_TABLE = "message_settings"
CHANNELS = ("email", "sms", "whatsapp")

__all__ = ["ReasonCode", "TemplateAction", "TemplateField", "TEMPLATES_TABLE", "SETTINGS_TABLE", "CHANNELS"]
