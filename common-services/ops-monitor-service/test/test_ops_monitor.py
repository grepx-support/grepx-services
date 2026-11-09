# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""ops-monitor-service: feed, geocoding, board, access and the HTTP surface - without a live hub."""
import io
import json
import threading
import time

from grepx_auth import JwtStrategy, TokenService
from grepx_config import Config

from access import Access
from board import Board, fill
from feed import Feed
from geocode import Geocoder, attempts, onemap
from web import make_app


class Clock:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


def row(status, **more):
    return {"status": status, "action": "BOOK", "from_service": "web-bff", "to_service": "booking-service",
            "trace_id": "tr1", "occurred_at": "2026-11-09T10:00:00+00:00", **more}


# ---------------- feed ----------------
def test_feed_keeps_only_the_envelope_and_configured_references():
    feed = Feed(refs=["event_id"])
    e = feed.add("booking_requests", "k1", row("NEW", event_id="E1", name="Ada Lovelace", phone="91234567", email="a@x.sg"))
    assert e["refs"] == {"event_id": "E1"} and e["action"] == "BOOK"
    assert "Ada" not in json.dumps(e) and "9123" not in json.dumps(e) and "@" not in json.dumps(e)


def test_feed_measures_new_to_verdict_on_its_own_clock_and_skips_repeats():
    clock = Clock()
    feed = Feed(clock=clock)
    feed.add("booking_requests", "k1", row("NEW"))
    clock.t += 0.042
    assert feed.add("booking_requests", "k1", row("CLAIMED"))["ms"] is None
    done = feed.add("booking_requests", "k1", row("ACCEPTED"))
    assert done["ms"] == 42
    assert feed.add("booking_requests", "k1", row("ACCEPTED")) is None          # recovery + live overlap
    assert feed.add("booking_requests", "k2", row("REJECTED", reason="FULL"))["ms"] is None   # NEW not seen


def test_feed_trace_stats_and_long_poll():
    feed = Feed()
    for i in range(30):
        feed.add("booking_requests", f"k{i}", row("NEW", trace_id=f"t{i}"))
        feed.add("booking_requests", f"k{i}", row("REJECTED" if i % 10 == 0 else "ACCEPTED", trace_id=f"t{i}", reason="FULL"))
    assert [e["status"] for e in feed.trace("t3")] == ["NEW", "ACCEPTED"]
    s = feed.stats(window_s=10 ** 9)
    assert (s["requests"], s["accepted"], s["rejected"]) == (30, 27, 3)
    assert s["reasons"] == [("FULL", 3)] and s["p95_ms"] is not None
    assert s["edges"] == [{"from": "web-bff", "to": "booking-service", "n": 30}]

    seq = feed.seq
    started = time.monotonic()
    assert feed.wait(seq, 0.05) == [] and time.monotonic() - started >= 0.04
    threading.Timer(0.05, lambda: feed.add("x_requests", "z", row("NEW"))).start()
    assert [e["key"] for e in feed.wait(seq, 2)] == ["z"]


def test_feed_window_is_bounded_and_counts_what_fell_off():
    feed = Feed(size=3)
    for i in range(5):
        feed.add("t", f"k{i}", row("NEW"))
    assert len(feed.since()) == 3 and feed.dropped == 2


def test_dead_letters_show_as_failures_of_the_service_named_on_them():
    e = Feed().add("dead_letters", "d1", {"service": "slot-service", "table": "slot_requests", "error": "boom", "trace_id": "t"})
    assert (e["status"], e["to_service"], e["reason"], e["source_table"]) == ("FAILED", "slot-service", "INTERNAL_ERROR", "slot_requests")


# ---------------- geocoding ----------------
class MemStore:
    def __init__(self):
        self.d = {}

    def get(self, c, k):
        return self.d.get((c, k))

    def put(self, c, k, v):
        self.d[(c, k)] = v


def test_geocode_tries_postal_code_then_text_then_first_part():
    assert attempts("Hall A, 1 Main Street, Singapore 529684") == ["529684", "Hall A, 1 Main Street, Singapore 529684", "Hall A"]


def test_geocode_known_wins_and_results_and_misses_are_cached():
    asked = []

    def get(url):
        asked.append(url)
        return {"results": [{"LATITUDE": "1.35", "LONGITUDE": "103.94"}]} if "529684" in url else {"results": []}

    store, clock = MemStore(), Clock()
    geo = Geocoder("onemap", known={"Central Hall": [103.85, 1.29]}, store=store, get=get, clock=clock)
    assert geo.locate("The Central Hall, level 2") == (103.85, 1.29) and asked == []
    assert geo.locate("1 Main St 529684") == (103.94, 1.35)
    assert geo.locate("1 Main St 529684") == (103.94, 1.35) and len(asked) == 1
    assert geo.locate("Nowhere") is None and geo.locate("Nowhere") is None and len(asked) == 2
    clock.t += 2 * 24 * 3600
    geo.locate("Nowhere")
    assert len(asked) == 3                                    # a miss is retried after a day


def test_geocode_network_failure_is_not_cached_and_pauses_lookups():
    asked = []

    def get(url):
        asked.append(url)
        raise OSError("down")
    store, clock = MemStore(), Clock()
    geo = Geocoder("nominatim", store=store, get=get, clock=clock)
    assert geo.locate("Somewhere 123456") is None and store.d == {}
    assert geo.locate("Elsewhere 654321") is None and len(asked) == 1        # paused, not hammered
    clock.t += 601
    geo.locate("Elsewhere 654321")
    assert len(asked) == 2


def test_onemap_reply_is_read_as_lng_lat():
    assert onemap("x", lambda url: {"results": [{"LATITUDE": "1.3", "LONGITUDE": "103.8"}]}) == (103.8, 1.3)


# ---------------- board ----------------
class FakeReader:
    def __init__(self, tables):
        self.tables, self.asked = tables, []

    def accepted(self, table, criteria=""):
        self.asked.append((table, criteria))
        return list(self.tables.get(table, []))

    def rows(self, table, criteria=""):
        return list(self.tables.get(table, []))

    def accepted_one(self, table, key):
        return next((r for r in self.tables.get(table, []) if r.get("_key") == key), None)


SETTINGS = {
    "places": {"table": "events", "id": "event_id", "label": "title", "address": "venue", "date": "event_date",
               "capacity": "capacity", "where": "event_date >= '{today}'",
               "known": {"Hall": [103.9, 1.35]},
               "counts": [{"name": "booked", "table": "bookings", "by": "event_id", "where": "state = 'confirmed'"}]},
    "kpis": [{"label": "Booked", "table": "bookings", "where": "state = 'confirmed'"},
             {"label": "Seats", "table": "events", "sum": "capacity"}],
}


def test_board_places_counts_and_kpis_from_settings_only():
    reader = FakeReader({
        "events": [{"_key": "E1", "event_id": "E1", "title": "Morning", "venue": "Town Hall", "event_date": "2026-11-10", "capacity": 40},
                   {"_key": "E2", "event_id": "E2", "title": "Evening", "venue": "Unknown place", "event_date": "2026-11-11", "capacity": "x"}],
        "bookings": [{"event_id": "E1"}, {"event_id": "E1"}, {"event_id": "E2"}],
    })
    board = Board(SETTINGS, reader, Geocoder(known=SETTINGS["places"]["known"]), day=lambda: "2026-11-09")
    places = board.places()
    assert [(p["id"], p["lng"], p["counts"]["booked"]) for p in places] == [("E1", 103.9, 2), ("E2", None, 1)]
    assert ("events", "event_date >= '2026-11-09'") in reader.asked
    assert board.kpis() == [{"label": "Booked", "value": 3, "of": None, "hint": ""}, {"label": "Seats", "value": 40, "of": None, "hint": ""}]
    assert Board({}, reader, Geocoder()).places() == []
    assert fill(None, "d") == ""


def test_board_refresh_keeps_the_last_good_value_when_a_read_fails():
    class Broken(FakeReader):
        def accepted(self, table, criteria=""):
            raise RuntimeError("hub down")
    board = Board(SETTINGS, FakeReader({"bookings": [{}]}), Geocoder(), day=lambda: "d")
    board.refresh("kpis")
    board.reader = Broken({})
    board.refresh("kpis")
    assert board.snapshot()["kpis"][0]["value"] == 1


# ---------------- access ----------------
TOKENS = TokenService(JwtStrategy("test-secret-of-at-least-32-bytes-long"))


def access(audience="admin", role="admin"):
    cfg = Config({"roles": {"member": "member", "staff": ["helper", "admin"], "admin": "admin"}, "monitor": {"audience": audience}})
    return Access(cfg, FakeReader({"user_access": [{"_key": "u1", "role": role}]}), tokens=TOKENS)


def bearer(sub="u1"):
    return "Bearer " + TOKENS.issue({"sub": sub, "role": "member"})


def test_access_needs_a_valid_token_and_the_configured_role():
    assert access().check("") == (401, "LOGIN_REQUIRED")
    assert access().check("Bearer nonsense") == (401, "INVALID_SESSION")
    assert access().check(bearer()) == (200, "u1")
    assert access(role="helper").check(bearer()) == (403, "FORBIDDEN")
    assert access("staff", role="helper").check(bearer()) == (200, "u1")
    assert access().check(bearer("someone-else")) == (403, "FORBIDDEN")    # token says member, no access row


# ---------------- http ----------------
class FakeMonitor:
    def __init__(self, allowed=True):
        self.feed = Feed()
        self.feed.add("booking_requests", "k1", row("NEW"))
        self.board = Board({}, FakeReader({}), Geocoder())
        self.allowed = allowed
        self.access = self

    def check(self, auth):
        return (200, "u1") if self.allowed else (401, "LOGIN_REQUIRED")

    def public_config(self):
        return {"title": "T"}


def call(app, path, query="", method="GET", auth="Bearer x"):
    out = {}

    def start(status, headers):
        out["status"], out["headers"] = status, dict(headers)
    body = b"".join(app({"PATH_INFO": path, "QUERY_STRING": query, "REQUEST_METHOD": method, "HTTP_AUTHORIZATION": auth,
                         "wsgi.input": io.BytesIO()}, start))
    return int(out["status"].split()[0]), out["headers"], body


def health(environ, start_response):
    start_response("200 OK", [("Content-Type", "text/plain")])
    return [b"ok"]


def test_http_serves_the_page_without_data_and_data_only_with_access():
    app = make_app(FakeMonitor(), health)
    status, headers, body = call(app, "/")
    assert status == 200 and b"<html" in body.lower()
    assert call(app, "/static/app.js")[0] == 200
    assert call(app, "/static/../web.py")[0] == 404
    assert call(app, "/health")[2] == b"ok"
    status, _, body = call(app, "/api/events", "after=0")
    assert status == 200 and json.loads(body)["events"][0]["key"] == "k1"
    assert json.loads(call(app, "/api/board", "window=1000000000")[2])["stats"]["requests"] == 1
    assert json.loads(call(app, "/api/trace/tr1")[2])["events"][0]["key"] == "k1"
    assert call(app, "/api/trace/bad id!")[0] == 404
    assert call(app, "/api/events", method="POST")[0] == 405
    locked = make_app(FakeMonitor(allowed=False), health)
    assert call(locked, "/api/events")[0] == 401 and call(locked, "/")[0] == 200
