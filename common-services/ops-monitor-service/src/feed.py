# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The live feed: every request row and verdict the monitor sees, as small safe events.

An event keeps only the envelope (table, key, status, action, reason, services, trace, hop, time) plus the configured
reference fields that place it (an event id, ...). Names, phones, emails and every other business field are never
copied - the monitor can be shown on a wall without exposing anyone.

Times: `at` is when the row says it happened (occurred_at) or, if absent, when the monitor saw it. `ms` (request ->
verdict) is measured on the monitor's own monotonic clock between seeing NEW and seeing the verdict, so it is the
time observed at the hub, never a cross-machine difference. A verdict whose NEW the monitor did not see has no ms.
"""
from __future__ import annotations

import threading
import time
from collections import Counter, OrderedDict, deque
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Optional

VERDICTS = ("ACCEPTED", "REJECTED")
OPEN = ("NEW", "CLAIMED")
FAILED = "FAILED"
DEAD = "dead_letters"
ENVELOPE = ("status", "action", "reason", "from_service", "to_service", "trace_id", "parent", "hop", "occurred_at", "error")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _short(value: Any, n: int = 160) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= n else text[: n - 1] + "…"


class Feed:
    """Bounded, thread-safe, in-memory event log with a sequence number clients can resume from."""

    def __init__(self, size: int = 5000, refs: Iterable[str] = (), clock: Callable[[], float] = time.monotonic):
        self.size, self.refs, self.clock = size, tuple(refs), clock
        self.events: deque[dict] = deque(maxlen=size)
        self.seq = 0
        self.dropped = 0                                   # events that fell off the end of the window
        self.cond = threading.Condition()
        self._seen: OrderedDict[tuple, str] = OrderedDict()   # (table, key) -> last status (skip repeats)
        self._opened: OrderedDict[tuple, float] = OrderedDict()   # (table, key) -> clock when NEW was seen
        self.started = time.time()

    # ---- writing ----
    def add(self, table: str, key: str, fields: dict, recovered: bool = False) -> Optional[dict]:
        status = str(fields.get("status") or "")
        if table == DEAD:
            status = FAILED
        with self.cond:
            ident = (table, key)
            if self._seen.get(ident) == status:
                return None                               # same row, same status: recovery and live overlap
            self._remember(self._seen, ident, status)
            ms = None
            if status == "NEW":
                self._remember(self._opened, ident, self.clock())
            elif status in VERDICTS or status == FAILED:
                opened = self._opened.pop(ident, None)
                if opened is not None:
                    ms = int((self.clock() - opened) * 1000)
            self.seq += 1
            event = {"seq": self.seq, "table": table, "key": key, "status": status, "ms": ms, "recovered": recovered,
                     "at": str(fields.get("occurred_at") or _now_iso()), "seen": _now_iso(),
                     **{f: _short(fields.get(f)) for f in ENVELOPE if f not in ("status", "occurred_at") and fields.get(f) not in (None, "")}}
            refs = {f: str(fields[f]) for f in self.refs if fields.get(f) not in (None, "")}
            if refs:
                event["refs"] = refs
            if table == DEAD:
                event["reason"] = event.get("reason") or "INTERNAL_ERROR"
                event["to_service"] = str(fields.get("service") or "")
                event["source_table"] = str(fields.get("table") or "")
            if len(self.events) == self.size:
                self.dropped += 1
            self.events.append(event)
            self.cond.notify_all()
            return event

    def _remember(self, store: OrderedDict, ident: tuple, value: Any) -> None:
        store[ident] = value
        store.move_to_end(ident)
        while len(store) > self.size * 4:
            store.popitem(last=False)

    # ---- reading ----
    def since(self, after: int = 0, limit: int = 500) -> list[dict]:
        with self.cond:
            return [e for e in self.events if e["seq"] > after][-limit:]

    def wait(self, after: int, timeout: float) -> list[dict]:
        """Events after `after`; blocks up to `timeout` seconds when there are none yet (long poll)."""
        deadline = time.monotonic() + max(0.0, timeout)
        with self.cond:
            while self.seq <= after:
                left = deadline - time.monotonic()
                if left <= 0:
                    break
                self.cond.wait(left)
        return self.since(after)

    def trace(self, trace_id: str) -> list[dict]:
        with self.cond:
            return sorted((e for e in self.events if e.get("trace_id") == trace_id), key=lambda e: e["seq"])

    def stats(self, window_s: float = 3600) -> dict:
        """Counts over the last window_s seconds of verdicts (by the monitor's wall clock)."""
        cutoff = time.time() - window_s
        with self.cond:
            recent = [e for e in self.events if _when(e) >= cutoff]
        verdicts = [e for e in recent if e["status"] in VERDICTS or e["status"] == FAILED]
        rejected = [e for e in verdicts if e["status"] != "ACCEPTED"]
        timed = sorted(e["ms"] for e in verdicts if e["ms"] is not None)
        last_min = time.time() - 60
        edges = Counter((e.get("from_service", ""), e.get("to_service", "")) for e in recent
                        if e["status"] == "NEW" and e.get("from_service") and e.get("to_service"))
        return {
            "window_s": window_s,
            "requests": sum(1 for e in recent if e["status"] == "NEW") or len(verdicts),
            "verdicts": len(verdicts), "accepted": len(verdicts) - len(rejected), "rejected": len(rejected),
            "per_minute": sum(1 for e in verdicts if _when(e) >= last_min),
            "p50_ms": _pct(timed, 50), "p95_ms": _pct(timed, 95), "timed": len(timed),
            "reasons": Counter(e.get("reason") or e["status"] for e in rejected).most_common(8),
            "by_service": Counter(e.get("to_service") or e["table"] for e in verdicts).most_common(),
            "edges": [{"from": a, "to": b, "n": n} for (a, b), n in edges.most_common(60)],
            "window_events": len(self.events), "dropped": self.dropped, "seq": self.seq,
        }


def _pct(values: list[int], p: int) -> Optional[int]:
    """Nearest-rank percentile; None until there are enough samples for it to mean something."""
    if len(values) < (20 if p >= 95 else 5):
        return None
    return values[min(len(values) - 1, max(0, int(round(p / 100 * len(values))) - 1))]


def _when(event: dict) -> float:
    """When it happened: the row's own time, else when the monitor saw it."""
    return _epoch(event["at"]) or _epoch(event["seen"])


def _epoch(iso: str) -> float:
    try:
        return datetime.fromisoformat(iso).timestamp()
    except (TypeError, ValueError):
        return 0.0
