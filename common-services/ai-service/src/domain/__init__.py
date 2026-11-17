# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Building what goes to the model, and calling it. No tables here."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

API = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-5-5"      # fast: an answer must come back within the 15 s a request may take (GREPX_AI_MODEL to change)
BASE = ("You are the assistant inside {product}, business software used by {business}. Answer in plain, short sentences "
        "for a busy shop owner or staff member. Use ONLY the business data given; if it does not hold the answer, say what "
        "is missing. Money is in {currency}. Never invent numbers, names or IMEIs. Today is {today}.")


def month(day: str) -> str:
    return day[:7]


def prompt(raw: dict) -> tuple[str, str]:
    """(system, user) for the model: the base rules + the feature's own instructions; the question + the data."""
    system = BASE.format(product=raw.get("product") or "GrepX", business=raw.get("business") or "a business",
                         currency=raw.get("currency") or "", today=raw.get("today") or "")
    if raw.get("instructions"):
        system += "\n\n" + str(raw["instructions"])[:4000]
    data = raw.get("data")
    text = json.dumps(data, ensure_ascii=False, default=str)[:60000] if data not in (None, "", {}, []) else ""
    user = (f"Business data (JSON):\n{text}\n\n" if text else "") + f"Question: {str(raw.get('question') or '').strip()[:2000]}"
    return system, user


def call_model(system: str, user: str, max_tokens: int = 700, env=os.environ) -> str:
    """One answer from the model (Anthropic Messages API). Raises KeyError without a key, RuntimeError on failure."""
    if env.get("GREPX_AI_FAKE"):                       # tests and demos without a key: a canned answer naming the question
        return "AI: " + user.rsplit("Question: ", 1)[-1][:120]
    key = env.get("GREPX_AI_KEY") or env.get("ANTHROPIC_API_KEY")
    if not key:
        raise KeyError("NO_KEY")
    body = json.dumps({"model": env.get("GREPX_AI_MODEL") or MODEL, "max_tokens": max_tokens, "system": system,
                       "messages": [{"role": "user", "content": user}]}).encode()
    req = urllib.request.Request(env.get("GREPX_AI_URL") or API, data=body, method="POST",
                                 headers={"content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=13) as r:
            out = json.loads(r.read())
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError(str(exc)) from exc
    return "".join(b.get("text", "") for b in out.get("content") or [] if b.get("type") == "text").strip()


__all__ = ["call_model", "month", "prompt"]
