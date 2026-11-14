# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Sign-in providers (Strategy + Registry): each proves who someone is from a provider token.
Adding Microsoft or Apple = one class + PROVIDERS entry; nothing else changes."""
from .base import Identity, IdentityError, IdentityProvider
from .google import GoogleProvider
from .oidc import CompanyProvider, MicrosoftProvider, OidcProvider

PROVIDERS: dict[str, IdentityProvider] = {p.name: p for p in (GoogleProvider(), MicrosoftProvider(), CompanyProvider())}

__all__ = ["OidcProvider", "Identity", "IdentityError", "IdentityProvider", "PROVIDERS"]
