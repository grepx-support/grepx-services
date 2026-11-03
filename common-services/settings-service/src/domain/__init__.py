"""Setting names: letters, digits, dots, dashes and underscores (e.g. SMTP_HOST, auto.welcome.channels). Pure."""
import re

NAME = re.compile(r"^[A-Za-z0-9_.\-]{1,120}$")
MAX_VALUE = 20_000


def valid_name(name: str) -> bool:
    return bool(NAME.match(name or ""))


__all__ = ["valid_name", "MAX_VALUE"]
