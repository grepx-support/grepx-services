"""auth-service: register, login, reset, password rules — against an in-memory Nexus."""
from pathlib import Path

import pytest
from grepx_auth import SecretBox, TokenService
from grepx_testkit.harness import ServiceHarness
from grepx_config import load_config

from repository import CredentialRepository
from routes import handle
from routes.common import Deps

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
SVC = "auth-service"


@pytest.fixture()
def h():
    Deps.repo, Deps.tokens, Deps.box = CredentialRepository(), TokenService.from_env(), SecretBox.from_env()
    harness = ServiceHarness().add(cfg, "auth_requests", handle, cfg.live_criteria)
    harness.add(cfg, "notifications", lambda *a: None)
    return harness


def call(h, **fields):
    return h.call("auth_requests", SVC, fields)


def register(h, email="ann@x.sg", password="secret123", user="u1"):
    return call(h, action="REGISTER", user_id=user, email=email, password_enc=Deps.box.seal(password))


def test_register_then_login_should_issue_sealed_token(h):
    assert register(h).ok
    v = call(h, action="LOGIN", email="ANN@x.sg", password_enc=Deps.box.seal("secret123"))
    assert v.ok and v.fields["role"] == "donor" and v.fields["password_enc"] == ""
    assert Deps.tokens.verify(Deps.box.open(v.fields["token_enc"]))["sub"] == "u1"


def test_wrong_password_should_reject_invalid_credentials(h):
    register(h)
    assert call(h, action="LOGIN", email="ann@x.sg", password_enc=Deps.box.seal("nope")).reason == "INVALID_CREDENTIALS"


def test_duplicate_email_should_reject_email_taken(h):
    register(h)
    assert register(h, user="u2").reason == "EMAIL_TAKEN"


def test_short_password_should_reject_weak_password(h):
    assert register(h, password="short").reason == "WEAK_PASSWORD"


def test_reset_flow_should_work_once(h):
    register(h)
    assert call(h, action="RESET_REQUEST", email="ann@x.sg", link_base="http://x/reset").ok
    note = h.rows("notifications")[0]
    token = note["values"]["link"].rsplit("/", 1)[1]
    first = call(h, action="RESET_CONFIRM", token_enc=Deps.box.seal(token), password_enc=Deps.box.seal("newpass123"))
    second = call(h, action="RESET_CONFIRM", token_enc=Deps.box.seal(token), password_enc=Deps.box.seal("other1234"))
    assert first.ok and second.reason == "INVALID_TOKEN"


def test_unknown_email_reset_should_still_accept(h):
    assert call(h, action="RESET_REQUEST", email="ghost@x.sg").ok
    assert h.rows("notifications") == []


def test_set_password_should_return_generated_temp_password(h):
    register(h)
    v = call(h, action="SET_PASSWORD", user_id="u1")
    temp = Deps.box.open(v.fields["temp_password_enc"])
    assert v.ok and call(h, action="LOGIN", email="ann@x.sg", password_enc=Deps.box.seal(temp)).ok


def test_rows_should_be_stamped_from_this_service(h):
    v = register(h)
    assert v.fields["from_service"] == SVC
    assert SVC in cfg.recovery_criteria and "to_service" in cfg.recovery_criteria


def test_set_password_for_a_new_person_should_replace_a_stale_credential_with_the_same_email(h):
    register(h, user="old-person", password="old-secret1")       # people records reset, auth database kept
    assert call(h, action="SET_PASSWORD", user_id="new-person", email="ann@x.sg", password_enc=Deps.box.seal("new-secret1")).ok
    v = call(h, action="LOGIN", email="ann@x.sg", password_enc=Deps.box.seal("new-secret1"))
    assert v.ok and v.fields["user_id"] == "new-person"


class FakeGoogle:
    """Stands in for Google: the 'token' is the email it vouches for."""
    name = "google"

    def configured(self, settings):
        return True

    def verify(self, token, settings):
        from providers import Identity, IdentityError
        if not token.endswith("@x.sg"):
            raise IdentityError("bad token")
        return Identity("google", f"sub-{token}", token, "Ann Tan")


@pytest.fixture()
def google(monkeypatch):
    import providers
    monkeypatch.setitem(providers.PROVIDERS, "google", FakeGoogle())


def google_login(h, email):
    return call(h, action="LOGIN_EXTERNAL", provider="google", id_token_enc=Deps.box.seal(email))


def test_google_login_should_sign_in_an_existing_account_with_its_role(h, google):
    register(h)                                              # a password account (donor, volunteer or admin)
    v = google_login(h, "ann@x.sg")
    assert v.ok and v.fields["registered"] is True and v.fields["user_id"] == "u1"
    assert Deps.tokens.verify(Deps.box.open(v.fields["token_enc"]))["sub"] == "u1"
    assert Deps.repo.by_id("u1").external == {"google": "sub-ann@x.sg"}


def test_google_login_without_account_should_say_so_then_link_creates_the_login(h, google):
    v = google_login(h, "new@x.sg")
    assert v.ok and v.fields["registered"] is False and v.fields["email"] == "new@x.sg" and v.fields["name"] == "Ann Tan"
    linked = call(h, action="LINK_EXTERNAL", user_id="p9", provider="google", id_token_enc=Deps.box.seal("new@x.sg"))
    assert linked.ok and linked.fields["user_id"] == "p9"
    assert google_login(h, "new@x.sg").fields["user_id"] == "p9"
    assert call(h, action="LOGIN", email="new@x.sg", password_enc=Deps.box.seal("")).reason == "INVALID_CREDENTIALS"


def test_google_login_should_reject_bad_tokens_and_unknown_providers(h, google):
    assert google_login(h, "evil@elsewhere.com").reason == "INVALID_TOKEN"
    assert call(h, action="LOGIN_EXTERNAL", provider="myspace", id_token_enc="x").reason == "UNKNOWN_PROVIDER"
