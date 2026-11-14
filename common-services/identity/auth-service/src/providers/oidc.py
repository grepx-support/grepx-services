# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Sign-in with any OpenID Connect provider (Template Method): the ID token's signature is checked against the
provider's published keys, then audience (our client id), expiry and issuer; subclasses say where the keys are, which
issuer is right and which claim holds the email."""
from __future__ import annotations

from functools import lru_cache

from .base import Identity, IdentityError, IdentityProvider


@lru_cache(maxsize=8)
def _keys(url: str):
    import jwt
    return jwt.PyJWKClient(url, cache_keys=True)


class OidcProvider(IdentityProvider):
    client_setting = ""

    def configured(self, settings: dict) -> bool:
        return bool(settings.get(self.client_setting))

    def keys_url(self, settings: dict) -> str:
        raise NotImplementedError

    def issuer_ok(self, issuer: str, claims: dict, settings: dict) -> bool:
        raise NotImplementedError

    def email_of(self, claims: dict) -> str:
        return str(claims.get("email") or "")

    def verify(self, token: str, settings: dict) -> Identity:
        import jwt
        try:
            key = _keys(self.keys_url(settings)).get_signing_key_from_jwt(token).key
            claims = jwt.decode(token, key, algorithms=["RS256"], audience=settings[self.client_setting], leeway=60)
        except Exception as exc:      # noqa: BLE001 - every token problem means "not signed in"
            raise IdentityError(str(exc)) from exc
        if not self.issuer_ok(str(claims.get("iss") or ""), claims, settings):
            raise IdentityError("token from another issuer")
        email = self.email_of(claims).lower()
        if "@" not in email:
            raise IdentityError("the provider gave no email address")
        return Identity(self.name, str(claims["sub"]), email, str(claims.get("name") or ""))


class MicrosoftProvider(OidcProvider):
    """Microsoft 365 / Entra ID work accounts and personal Microsoft accounts. MICROSOFT_TENANT limits sign-in to one
    organisation (its tenant id); empty = any Microsoft account."""
    name, client_setting = "microsoft", "MICROSOFT_CLIENT_ID"

    def keys_url(self, settings: dict) -> str:
        return f"https://login.microsoftonline.com/{settings.get('MICROSOFT_TENANT') or 'common'}/discovery/v2.0/keys"

    def issuer_ok(self, issuer: str, claims: dict, settings: dict) -> bool:
        tenant = settings.get("MICROSOFT_TENANT") or claims.get("tid", "")
        return issuer == f"https://login.microsoftonline.com/{tenant}/v2.0" and (not settings.get("MICROSOFT_TENANT") or claims.get("tid") == tenant)

    def email_of(self, claims: dict) -> str:
        return str(claims.get("email") or claims.get("preferred_username") or "")


class CompanyProvider(OidcProvider):
    """Any company sign-in that speaks OpenID Connect (Okta, Auth0, Keycloak, Zoho, OneLogin, Azure B2C...):
    OIDC_ISSUER is its address, OIDC_CLIENT_ID our app's id there."""
    name, client_setting = "company", "OIDC_CLIENT_ID"

    def configured(self, settings: dict) -> bool:
        return bool(settings.get("OIDC_CLIENT_ID") and settings.get("OIDC_ISSUER"))

    def keys_url(self, settings: dict) -> str:
        import requests
        issuer = settings["OIDC_ISSUER"].rstrip("/")
        return requests.get(f"{issuer}/.well-known/openid-configuration", timeout=10).json()["jwks_uri"]

    def issuer_ok(self, issuer: str, claims: dict, settings: dict) -> bool:
        return issuer.rstrip("/") == settings["OIDC_ISSUER"].rstrip("/")
