# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""questionnaire-service: HSA rules via the form and the LifeBot chat flow."""
from datetime import date
from pathlib import Path

import pytest
from grepx_testkit.harness import ServiceHarness
from grepx_config import load_config

from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
OK = {"dob": "1990-01-01", "sex": "Female", "weight": "60"}


@pytest.fixture()
def h():
    return ServiceHarness().add(cfg, "questionnaire_requests", handle, cfg.live_criteria)


def check(h, **answers):
    return h.call("questionnaire_requests", "questionnaire-service", {"action": "CHECK", "answers": {**OK, **answers}})


def test_healthy_adult_should_be_eligible(h):
    v = check(h)
    assert v.fields["eligible"] is True and v.fields["reasons"] == []


@pytest.mark.parametrize("answers,fragment", [
    ({"weight": "40"}, "45 kg"), ({"fever": "yes"}, "fever"), ({"tattoo": "yes"}, "Tattoo"),
    ({"pregnant": "yes"}, "Pregnancy"), ({"hb": "11"}, "12.5"), ({"last": date.today().isoformat()}, "90 days"),
])
def test_rule_should_block_with_reason(h, answers, fragment):
    v = check(h, **answers)
    assert v.fields["eligible"] is False and any(fragment in r for r in v.fields["reasons"])


def test_minor_should_get_consent_note(h):
    sixteen = date.today().replace(year=date.today().year - 16, day=1).isoformat()
    assert any("consent" in n for n in check(h, dob=sixteen).fields["notes"])


def test_bad_answers_should_reject(h):
    assert h.call("questionnaire_requests", "questionnaire-service", {"action": "CHECK", "answers": {"dob": "x"}}).reason == "INVALID_ANSWERS"


def test_chat_should_walk_questions_and_conclude(h):
    state, reply = {}, None
    for message in ["", "30", "60", "Female", "No", "No", "No", "No", "No", "No", "No"]:
        v = h.call("questionnaire_requests", "questionnaire-service", {"action": "CHAT", "state": state, "message": message})
        state, reply = v.fields["state"], v.fields["reply"]
    assert reply.get("eligible") is True and reply["progress"] == 100


def test_criteria_should_publish_the_numbers_the_rules_use(h):
    c = h.call("questionnaire_requests", "questionnaire-service", {"action": "CRITERIA"}).fields["criteria"]
    assert c["WEIGHT_MIN"] == 45 and c["ADVISORY"]["wait_months"] == 4 and len(c["REQUIREMENTS"]) == 6


def test_without_a_product_plugin_it_says_so(h):
    bare = ServiceHarness().add({**cfg, "plugins": {}}, "questionnaire_requests", handle, cfg.live_criteria)
    assert bare.call("questionnaire_requests", "questionnaire-service", {"action": "CRITERIA"}).reason == "NOT_CONFIGURED"
