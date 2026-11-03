"""What every sign-in provider gives back: a verified email (the account key) and a display name."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class IdentityError(ValueError):
    """The token is not valid for this site (bad signature, wrong audience, expired, email not verified)."""


@dataclass(frozen=True)
class Identity:
    provider: str
    subject: str      # the provider's stable id for the person
    email: str
    name: str = ""


class IdentityProvider(ABC):
    name = ""

    @abstractmethod
    def configured(self, settings: dict) -> bool: ...

    @abstractmethod
    def verify(self, token: str, settings: dict) -> Identity: ...
