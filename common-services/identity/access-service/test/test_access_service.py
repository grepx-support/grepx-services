# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""access-service: roles, volunteer roles, personal permissions, admin safety rules."""
from pathlib import Path

import pytest
from grepx_testkit.harness import ServiceHarness
from grepx_config import load_config

from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")


@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, "access_requests", handle, cfg.live_criteria)
    for perm in ("checkin", "manage_drives", "reports"):
        harness.seed("permission_catalog", perm, {})
    return harness


def call(h, **f):
    return h.call("access_requests", "access-service", f)


def access(h, user):
    return h.read.accepted_one("user_access", user)


def test_volunteer_effective_permissions_should_union_role_and_personal(h):
    role = call(h, action="SAVE_ROLE", name="Check-in desk", perms=["checkin", "bogus"])
    call(h, action="SET_ROLE", user_id="u1", role="volunteer")
    call(h, action="SET_STAFF_ROLE", user_id="u1", staff_role_id=role.fields["role_id"])
    call(h, action="SET_PERMISSION", user_id="u1", perm="reports", enabled=True)
    assert access(h, "u1")["effective"] == ["checkin", "reports"]


def test_admin_should_have_every_permission(h):
    call(h, action="SET_ROLE", user_id="a1", role="admin")
    assert access(h, "a1")["effective"] == ["*"]


def test_admin_cannot_demote_self(h):
    call(h, action="SET_ROLE", user_id="a1", role="admin")
    call(h, action="SET_ROLE", user_id="a2", role="admin")
    assert call(h, action="SET_ROLE", user_id="a1", role="donor", actor_id="a1").reason == "SELF_DEMOTION"


def test_last_admin_should_stay_admin(h):
    call(h, action="SET_ROLE", user_id="a1", role="admin")
    assert call(h, action="SET_ROLE", user_id="a1", role="donor", actor_id="x").reason == "LAST_ADMIN"


def test_unknown_permission_should_reject(h):
    assert call(h, action="SET_PERMISSION", user_id="u1", perm="fly").reason == "UNKNOWN_PERMISSION"


def test_deleting_role_should_refresh_members(h):
    role = call(h, action="SAVE_ROLE", name="Desk", perms=["checkin"]).fields["role_id"]
    call(h, action="SET_ROLE", user_id="u1", role="volunteer")
    call(h, action="SET_STAFF_ROLE", user_id="u1", staff_role_id=role)
    assert call(h, action="DELETE_ROLE", role_id=role).ok
    assert access(h, "u1")["effective"] == []


def test_rows_should_be_stamped_from_this_service(h):
    assert call(h, action="SET_ROLE", user_id="u1", role="donor").fields["from_service"] == "access-service"


def test_register_permission_should_add_to_the_catalogue(h):
    assert call(h, action="REGISTER_PERMISSION", perm="export", label="Export data").ok
    assert h.read.accepted_one("permission_catalog", "export")["label"] == "Export data"
    assert not call(h, action="REGISTER_PERMISSION").ok
