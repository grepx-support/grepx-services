# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""ai-service: the business's data and the question go to the model; off, no key, the monthly limit, a failed call."""
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

import routes
from domain import call_model, prompt

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
T = "ai_requests"


def test_prompt_carries_rules_data_and_question():
    system, user = prompt({"product": "GrepX Electronics", "business": "Galaxy", "currency": "INR", "today": "2026-11-17",
                           "instructions": "Answer in one line.", "question": " Best seller? ", "data": {"top": [["S25", 12]]}})
    assert "GrepX Electronics" in system and "Never invent numbers" in system and system.endswith("Answer in one line.")
    assert user == 'Business data (JSON):\n{"top": [["S25", 12]]}\n\nQuestion: Best seller?'


def test_no_key_is_said_not_guessed():
    with pytest.raises(KeyError):
        call_model("s", "u", env={})


@pytest.fixture()
def h(monkeypatch):
    seen = []
    def fake(system, user, max_tokens):
        seen.append(user)
        if "fail" in user:
            raise RuntimeError("overloaded")
        if "nokey" in user:
            raise KeyError("NO_KEY")
        return "Galaxy S25 sold most: 12."
    monkeypatch.setattr(routes, "MODEL_CALL", fake)
    harness = ServiceHarness().add(cfg, T, routes.handle, cfg.live_criteria)
    harness.seen = seen
    return harness


def call(h, **f):
    return h.call(T, "ai-service", {"tenant_id": "gm", **f})


def test_ask_counts_and_limits(h):
    r = call(h, action="ASK", feature="ask", question="Best seller?", data={"top": [["S25", 12]]}, limit=2)
    assert r.ok and r.fields["answer"] == "Galaxy S25 sold most: 12." and r.fields["used"] == 1
    assert call(h, action="ASK", feature="brief", question="Morning brief", limit=2).fields["used"] == 2
    assert call(h, action="ASK", question="again", limit=2).reason == "LIMIT_REACHED"
    use = call(h, action="USAGE", limit=2).fields["usage"]
    assert use["calls"] == 2 and use["by_feature"] == {"ask": 1, "brief": 1}
    assert call(h, action="ASK", question="x", enabled=False).reason == "AI_OFF"
    assert call(h, tenant_id="other", action="ASK", question="please fail").reason == "MODEL_FAILED"
    assert call(h, tenant_id="other", action="ASK", question="nokey").reason == "NO_KEY"
    assert call(h, tenant_id="other", action="USAGE").fields["usage"]["calls"] == 0          # failures are not counted
    assert call(h, action="ASK", question="  ").reason == "NO_QUESTION"
