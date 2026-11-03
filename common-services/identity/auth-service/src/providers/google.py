"""Google: verify the ID token (signature, audience = our client id, expiry) with google-auth; email must be verified."""
from __future__ import annotations

from .base import Identity, IdentityError, IdentityProvider


class GoogleProvider(IdentityProvider):
    name = "google"

    def configured(self, settings: dict) -> bool:
        return bool(settings.get("GOOGLE_CLIENT_ID"))

    def verify(self, token: str, settings: dict) -> Identity:
        from google.auth.transport.requests import Request
        from google.oauth2 import id_token
        try:
            claims = id_token.verify_oauth2_token(token, Request(), audience=settings["GOOGLE_CLIENT_ID"])
        except ValueError as exc:
            raise IdentityError(str(exc)) from exc
        if not claims.get("email") or not claims.get("email_verified"):
            raise IdentityError("Google has not verified this email address")
        return Identity(self.name, str(claims["sub"]), str(claims["email"]).lower(), str(claims.get("name") or ""))
