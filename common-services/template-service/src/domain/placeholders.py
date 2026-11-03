"""Custom wording may only use the placeholders the template declares."""
import re

PATTERN = re.compile(r"\{(\w+)\}")


def placeholders_in(*texts: str) -> set[str]:
    return {m for t in texts for m in PATTERN.findall(t or "")}
