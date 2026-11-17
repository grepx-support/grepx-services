# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Building what goes to the model, and calling it. No tables here.

Engines, first that applies:
  GREPX_AI_FAKE=1          a canned answer (tests, demos)
  GREPX_AI_KEY / ANTHROPIC_API_KEY   Anthropic Claude (GREPX_AI_MODEL, default below)
  otherwise                the free local engine, Ollama at GREPX_OLLAMA_URL (default http://127.0.0.1:11434): the
                           product's own model (grepx-<product>, built from its context by platform/ai-engine), else
                           GREPX_AI_BASE (default qwen2.5:3b)."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

ANTHROPIC = "https://api.anthropic.com/v1/messages"
CLAUDE = "claude-haiku-5-5"
OLLAMA = "http://127.0.0.1:11434"
BASE_MODEL = "qwen2.5:3b"
HISTORY = 12                      # chat messages sent back to the model
RULES = ("You are the assistant inside {product}, business software used by {business}. Answer in plain, short sentences "
         "for a busy owner or staff member. Use ONLY the business data given; if it does not hold the answer, say what is "
         "missing. Money is in {currency}. Never invent numbers, names or IDs. Today is {today}.")


def month(day: str) -> str:
    return day[:7]


def system_prompt(raw: dict) -> str:
    """The rules + the product's own context (what the product is, its words, its screens) + the feature's instructions."""
    s = RULES.format(product=raw.get("product") or "GrepX", business=raw.get("business") or "a business",
                     currency=raw.get("currency") or "", today=raw.get("today") or "")
    if raw.get("context"):
        s += "\n\nAbout this product:\n" + str(raw["context"])[:12000]
    if raw.get("instructions"):
        s += "\n\n" + str(raw["instructions"])[:4000]
    return s


def with_data(question: str, data) -> str:
    text = json.dumps(data, ensure_ascii=False, default=str)[:40000] if data not in (None, "", {}, []) else ""
    return (f"Business data (JSON):\n{text}\n\n" if text else "") + f"Question: {str(question or '').strip()[:4000]}"


def prompt(raw: dict) -> tuple[str, str]:
    """(system, user) for one question."""
    return system_prompt(raw), with_data(raw.get("question"), raw.get("data"))


def _post(url: str, body: dict, headers: dict, timeout: float) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST", headers={"content-type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def call_model(system: str, messages: list[dict], max_tokens: int = 700, model: str = "", env=os.environ) -> str:
    """One answer. messages = [{role: user|assistant, content}]. KeyError: no engine reachable; RuntimeError: it failed."""
    if env.get("GREPX_AI_FAKE"):
        return "AI: " + messages[-1]["content"].rsplit("Question: ", 1)[-1][:120]
    key = env.get("GREPX_AI_KEY") or env.get("ANTHROPIC_API_KEY")
    try:
        if key:
            out = _post(env.get("GREPX_AI_URL") or ANTHROPIC, {"model": env.get("GREPX_AI_MODEL") or CLAUDE, "max_tokens": max_tokens, "system": system,
                                                              "messages": messages}, {"x-api-key": key, "anthropic-version": "2023-06-01"}, 90)
            return "".join(b.get("text", "") for b in out.get("content") or [] if b.get("type") == "text").strip()
        return ollama(system, messages, max_tokens, model, env)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"{exc.code} {exc.reason}") from exc
    except (urllib.error.URLError, ConnectionError) as exc:
        if not key:
            raise KeyError("NO_KEY") from exc          # no local engine running
        raise RuntimeError(str(exc)) from exc
    except (TimeoutError, ValueError) as exc:
        raise RuntimeError(str(exc)) from exc


def ollama(system: str, messages: list[dict], max_tokens: int, model: str, env) -> str:
    """The local engine: the product's own model if it has been built, else the base model."""
    url = (env.get("GREPX_OLLAMA_URL") or OLLAMA).rstrip("/") + "/api/chat"
    base = env.get("GREPX_AI_BASE") or BASE_MODEL
    body = {"messages": [{"role": "system", "content": system}, *messages], "stream": False, "options": {"num_predict": max_tokens, "temperature": 0.3}}
    for name in [m for m in (env.get("GREPX_AI_MODEL") or model, base) if m]:
        try:
            return str(_post(url, {**body, "model": name}, {}, 180).get("message", {}).get("content", "")).strip()
        except urllib.error.HTTPError as exc:
            if exc.code != 404 or name == base:           # 404: that model is not built here - try the base model
                raise
    raise RuntimeError("no model")


def title_of(text: str) -> str:
    words = " ".join(str(text).split())
    return words[:60] + ("…" if len(words) > 60 else "")


__all__ = ["HISTORY", "call_model", "month", "prompt", "system_prompt", "title_of", "with_data"]
