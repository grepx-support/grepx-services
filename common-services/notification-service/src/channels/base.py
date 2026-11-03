# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Channel strategy: one class per delivery mechanism."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ChannelResult:
    delivery: str
    error: str = ""


class Channel(ABC):
    name: str = ""

    @abstractmethod
    def configured(self) -> bool: ...

    @abstractmethod
    def send(self, recipient: str, subject: str, body: str, html: str | None) -> None: ...

    def check(self) -> str:
        """Sign in to the provider without sending anything; a readable confirmation, or raise with the provider's error."""
        raise NotImplementedError(f"{self.name} has no connection test")
