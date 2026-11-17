# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""ai-service: a question or a chat message becomes a job, answered in the background by the model; the switch, the
month's limit, a failed or missing engine; chats are one person's own; the local engine falls back to the base model."""
import json
import urllib.error
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

import domain
import importlib
import routes
from domain import call_model, prompt, system_prompt

answering = importlib.import_module("jobs.answer")       # the module (the package exports its function under the same name)

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
T = "ai_requests"


def test_prompt_carries_rules_context_data_and_question():
    system, user = prompt({"product": "GrepX Electronics", "business": "Galaxy", "currency": "INR", "today": "2026-11-17", "context": "IMEI = phone id.",
                           "instructions": "Answer in one line.", "question": " Best seller? ", "data": {"top": [["S25", 12]]}})
    assert "Never invent numbers" in system and "About this product:\nIMEI = phone id." in system and system.endswith("Answer in one line.")
    assert user == 'Business data (JSON):\n{"top": [["S25", 12]]}\n\nQuestion: Best seller?'


def test_engines(monkeypatch):
    assert call_model("s", [{"role": "user", "content": "Question: hi"}], env={"GREPX_AI_FAKE": "1"}) == "AI: hi"
    with pytest.raises(KeyError):                                     # no key and no local engine running
        call_model("s", [{"role": "user", "content": "x"}], env={"GREPX_OLLAMA_URL": "http://127.0.0.1:1"})
    sent = []
    def post(url, body, headers, timeout):
        sent.append((url, body["model"]))
        if body["model"] == "grepx-shop":
            raise urllib.error.HTTPError(url, 404, "not found", {}, None)
        return {"message": {"content": " Fine. "}}
    monkeypatch.setattr(domain, "_post", post)
    assert call_model("s", [{"role": "user", "content": "x"}], model="grepx-shop", env={}) == "Fine."
    assert sent == [("http://127.0.0.1:11434/api/chat", "grepx-shop"), ("http://127.0.0.1:11434/api/chat", "qwen2.5:3b")]   # not built: the base model


@pytest.fixture()
def h(monkeypatch):
    def fake(system, messages, max_tokens, model):
        q = messages[-1]["content"]
        if "fail" in q:
            raise RuntimeError("overloaded")
        if "nokey" in q:
            raise KeyError("NO_KEY")
        return f"answer {len(messages)} via {model or 'base'}"
    monkeypatch.setattr(answering, "MODEL_CALL", fake)
    return (ServiceHarness().add(cfg, T, routes.handle, cfg.live_criteria)
            .add(cfg, "ai_jobs", answering.answer, "status = 'ACCEPTED' AND state = 'thinking'"))      # as config.yaml subscribes


def call(h, **f):
    return h.call(T, "ai-service", {"tenant_id": "gm", "actor_id": "u1", **f})


def job(h, key):
    return {r["_key"]: r for r in h.rows("ai_jobs")}[key]


def test_ask_is_a_job_answered_in_the_background(h):
    r = call(h, action="ASK", feature="ask", question="Best seller?", data={"top": 1}, model="grepx-electronics", limit=2)
    assert r.ok and r.fields["job"]["state"] == "thinking"
    h.settle()
    done = job(h, r.fields["job"]["job_id"])
    assert done["state"] == "done" and done["answer"] == "answer 1 via grepx-electronics" and "system" not in done
    assert call(h, action="ASK", feature="brief", question="Morning brief", limit=2).ok
    h.settle()
    assert call(h, action="ASK", question="again", limit=2).reason == "LIMIT_REACHED"
    assert call(h, action="USAGE", limit=2).fields["usage"] == {"tenant_id": "gm", "month": call(h, action="USAGE").fields["usage"]["month"],
                                                                 "calls": 2, "by_feature": {"ask": 1, "brief": 1}}
    assert call(h, action="ASK", question="x", enabled=False).reason == "AI_OFF"
    bad = call(h, tenant_id="other", action="ASK", question="please fail")
    nokey = call(h, tenant_id="other", action="ASK", question="nokey")
    h.settle()
    assert job(h, bad.fields["job"]["job_id"])["reason"] == "MODEL_FAILED" and job(h, nokey.fields["job"]["job_id"])["reason"] == "NO_KEY"
    assert call(h, tenant_id="other", action="USAGE").fields["usage"]["calls"] == 0          # failures are not counted
    assert call(h, action="ASK", question="  ").reason == "NO_QUESTION"


def test_chat_keeps_history_and_is_private(h):
    first = call(h, action="CHAT", message="Which phones sold most?", data={"x": 1}, product="GrepX Electronics")
    chat = first.fields["chat"]
    assert chat["title"] == "Which phones sold most?" and chat["thinking"]
    h.settle()
    rows = {r["_key"]: r for r in h.rows("ai_chats")}
    msgs = rows[chat["chat_id"]]["messages"]
    assert [m["role"] for m in msgs] == ["user", "assistant"] and msgs[1]["content"] == "answer 1 via base" and not rows[chat["chat_id"]]["thinking"]
    assert call(h, action="CHAT", chat_id=chat["chat_id"], message="and laptops?").ok
    h.settle()
    msgs = {r["_key"]: r for r in h.rows("ai_chats")}[chat["chat_id"]]["messages"]
    assert msgs[-1]["content"] == "answer 3 via base"                                   # the earlier exchange went with it
    assert call(h, actor_id="u2", action="CHAT", chat_id=chat["chat_id"], message="peek").reason == "UNKNOWN_CHAT"
    assert call(h, actor_id="u2", action="CHAT_DELETE", chat_id=chat["chat_id"]).reason == "UNKNOWN_CHAT"
    assert call(h, action="CHAT_DELETE", chat_id=chat["chat_id"]).ok
    assert {r["_key"]: r for r in h.rows("ai_chats")}[chat["chat_id"]]["deleted"] is True
