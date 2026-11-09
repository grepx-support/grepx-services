# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The monitor's HTTP surface - plain WSGI, standard library only (config.yaml `web_app:`).

    GET /                     the live screen (static page; it asks for a login before showing anything)
    GET /static/<file>        its script and styles
    GET /api/config           title, map centre, words                       \
    GET /api/events?after=N   events after N; waits up to `wait` s for new     |  bearer token of an allowed role
    GET /api/board            places, headline numbers, services, stats        |  (see access.py)
    GET /api/trace/<id>       every event of one trace the monitor has seen   /
    GET /health, /metrics     as every service

It listens on 127.0.0.1 (GREPX_BIND); people reach it through the product's web address at /ops/, which the BFF
passes through unchanged.
"""
from __future__ import annotations

import json
import mimetypes
import re
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs

STATIC = Path(__file__).resolve().parent / "static"
HEADERS = [("X-Content-Type-Options", "nosniff"), ("Referrer-Policy", "no-referrer"), ("Cache-Control", "no-store")]
TRACE = re.compile(r"^/api/trace/([A-Za-z0-9_\-]{1,64})$")


def _json(start_response: Callable, status: int, body: Any) -> list[bytes]:
    data = json.dumps(body, default=str).encode()
    start_response(f"{status} {_REASONS.get(status, 'OK')}", [("Content-Type", "application/json"), ("Content-Length", str(len(data))), *HEADERS])
    return [data]


_REASONS = {200: "OK", 401: "Unauthorized", 403: "Forbidden", 404: "Not Found", 405: "Method Not Allowed"}


def _file(start_response: Callable, path: Path) -> list[bytes]:
    data = path.read_bytes()
    ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if ctype.startswith("text/") or ctype.endswith("javascript"):
        ctype += "; charset=utf-8"
    start_response("200 OK", [("Content-Type", ctype), ("Content-Length", str(len(data))), *HEADERS])
    return [data]


def make_app(m: Any, health: Callable) -> Callable:
    def app(environ, start_response):
        path = environ.get("PATH_INFO") or "/"
        if path in ("/health", "/metrics"):
            return health(environ, start_response)
        if environ.get("REQUEST_METHOD", "GET") not in ("GET", "HEAD"):
            return _json(start_response, 405, {"error": "METHOD_NOT_ALLOWED"})
        if path in ("/", "/index.html"):
            return _file(start_response, STATIC / "index.html")
        if path.startswith("/static/"):
            target = (STATIC / path[len("/static/"):]).resolve()
            if STATIC in target.parents and target.is_file():
                return _file(start_response, target)
            return _json(start_response, 404, {"error": "NOT_FOUND"})
        if not path.startswith("/api/"):
            return _json(start_response, 404, {"error": "NOT_FOUND"})

        status, who = m.access.check(environ.get("HTTP_AUTHORIZATION", ""))
        if status != 200:
            return _json(start_response, status, {"error": who})
        query = {k: v[-1] for k, v in parse_qs(environ.get("QUERY_STRING", "")).items()}
        if path == "/api/config":
            return _json(start_response, 200, m.public_config())
        if path == "/api/events":
            after = _int(query.get("after"), 0)
            wait = min(25.0, max(0.0, float(_int(query.get("wait"), 0))))
            events = m.feed.wait(after, wait) if wait else m.feed.since(after)
            return _json(start_response, 200, {"seq": m.feed.seq, "events": events})
        if path == "/api/board":
            return _json(start_response, 200, {**m.board.snapshot(), "stats": m.feed.stats(_int(query.get("window"), 3600))})
        found = TRACE.match(path)
        if found:
            return _json(start_response, 200, {"trace_id": found.group(1), "events": m.feed.trace(found.group(1))})
        return _json(start_response, 404, {"error": "NOT_FOUND"})
    return app


def _int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def create_app(cfg: Any, health: Callable) -> Callable:
    """config.yaml `web_app:`"""
    from monitor import monitor
    return make_app(monitor(cfg), health)
