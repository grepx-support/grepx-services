"""Sign-in providers (Strategy + Registry): each proves who someone is from a provider token.
Adding Microsoft or Apple = one class + PROVIDERS entry; nothing else changes."""
from .base import Identity, IdentityError, IdentityProvider
from .google import GoogleProvider

PROVIDERS: dict[str, IdentityProvider] = {p.name: p for p in (GoogleProvider(),)}

__all__ = ["Identity", "IdentityError", "IdentityProvider", "PROVIDERS"]
