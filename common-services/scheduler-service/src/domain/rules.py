# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""A schedule's rule - when it fires - one class per kind behind one interface (Strategy), made by rule_of (Factory):
due(now, since) = the slot to fire now (the latest firing time after `since` and not after `now`), or None;
upcoming(after, n) = the next n firing times; words = the rule as people say it. Pure: no I/O, no clock."""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, tzinfo
from typing import Optional
from zoneinfo import ZoneInfo

from apscheduler.triggers.cron import CronTrigger

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
LOOK_BACK = timedelta(days=8)          # how far back a missed slot is still fired once (the service was down)


def zone(name: str) -> tzinfo:
    try:
        return ZoneInfo(name or "UTC")
    except Exception as exc:
        raise ValueError("INVALID_TIMEZONE") from exc


def slot_of(at: datetime) -> str:
    return f"{at:%Y%m%dT%H%M}"


class Rule(ABC):
    @abstractmethod
    def due(self, now: datetime, since: Optional[datetime] = None) -> Optional[str]: ...

    @abstractmethod
    def upcoming(self, after: datetime, n: int = 5) -> list[datetime]: ...

    @property
    @abstractmethod
    def words(self) -> str: ...


class EveryMinutes(Rule):
    """Every N minutes from midnight (the slot is the start of the current window)."""

    def __init__(self, minutes: int):
        if minutes <= 0:
            raise ValueError("INVALID_SCHEDULE")
        self.minutes = minutes

    def due(self, now, since=None):
        m = (now.hour * 60 + now.minute) // self.minutes * self.minutes
        return f"{now:%Y%m%d}T{m // 60:02d}{m % 60:02d}"

    def upcoming(self, after, n=5):
        start = after.replace(second=0, microsecond=0)
        m = (start.hour * 60 + start.minute) // self.minutes * self.minutes
        first = start.replace(hour=0, minute=0) + timedelta(minutes=m + self.minutes)
        return [first + timedelta(minutes=self.minutes * i) for i in range(n)]

    @property
    def words(self):
        return f"every {self.minutes} minutes"


class DailyAt(Rule):
    """Once a day at HH:MM (local time of the clock given); due from that time until midnight."""

    def __init__(self, at: str):
        try:
            self.hour, self.minute = (int(x) for x in at.split(":"))
            assert 0 <= self.hour < 24 and 0 <= self.minute < 60
        except Exception as exc:
            raise ValueError("INVALID_SCHEDULE") from exc
        self.at = at

    def due(self, now, since=None):
        return f"{now:%Y%m%d}" if (now.hour, now.minute) >= (self.hour, self.minute) else None

    def upcoming(self, after, n=5):
        first = after.replace(hour=self.hour, minute=self.minute, second=0, microsecond=0)
        first = first if first > after else first + timedelta(days=1)
        return [first + timedelta(days=i) for i in range(n)]

    @property
    def words(self):
        return f"every day at {self.at}"


class Cron(Rule):
    """Any cron line in a timezone (APScheduler's CronTrigger does the calendar - day lengths, DST, month ends)."""

    def __init__(self, line: str, tz: str = "UTC"):
        self.line, self.tz = " ".join((line or "").split()), tz or "UTC"
        z = zone(self.tz)
        try:
            self.trigger = CronTrigger.from_crontab(standard(self.line), timezone=z)
        except Exception as exc:
            raise ValueError("INVALID_SCHEDULE") from exc

    def _next(self, after: datetime) -> Optional[datetime]:
        return self.trigger.get_next_fire_time(None, after)

    def due(self, now, since=None):
        start = max(since or now - LOOK_BACK, now - LOOK_BACK)
        last, at = None, self._next(start + timedelta(seconds=1))
        while at is not None and at <= now:
            last, at = at, self._next(at + timedelta(seconds=1))
        return slot_of(last.astimezone(zone("UTC"))) if last else None

    def upcoming(self, after, n=5):
        out, at = [], after
        for _ in range(n):
            at = self._next(at + timedelta(seconds=1))
            if at is None:
                break
            out.append(at)
        return out

    @property
    def words(self):
        return words_of(self.line, self.tz)


WEEKDAY = ["sun", "mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def standard(line: str) -> str:
    """Cron counts weekdays from Sunday = 0 (7 too); APScheduler 3 from Monday = 0 - so the weekday numbers become names."""
    p = line.split()
    if len(p) == 5:
        p[4] = re.sub(r"\d+", lambda m: WEEKDAY[int(m.group())] if int(m.group()) <= 7 else m.group(), p[4]) if not p[4].startswith("*/") else p[4]
    return " ".join(p)


def words_of(line: str, tz: str) -> str:
    """20 0 * * * -> "every day at 00:20 UTC" - the common shapes in words, any other line as it is."""
    p = line.split()
    if len(p) != 5:
        return line
    m, h, dom, mon, dow = p
    at = f"{int(h):02d}:{int(m):02d} {tz}" if m.isdigit() and h.isdigit() else ""
    if at and dom == mon == dow == "*":
        return f"every day at {at}"
    if at and dom == mon == "*" and dow in ("1-5", "mon-fri"):
        return f"weekdays at {at}"
    if at and dom == mon == "*" and dow.isdigit() and int(dow) <= 7:
        return f"every {DAYS[(int(dow) - 1) % 7]} at {at}"
    if at and dow == mon == "*" and dom.isdigit():
        return f"on day {dom} of every month at {at}"
    if m.isdigit() and h == "*" and dom == mon == dow == "*":
        return f"every hour at :{int(m):02d}"
    if m.isdigit() and h.startswith("*/") and dom == mon == dow == "*":
        return f"every {h[2:]} hours at :{int(m):02d} ({tz})"
    return f"{line} ({tz})"


def rule_of(kind: str, every_minutes: int = 0, at: str = "", cron: str = "", tz: str = "") -> Rule:
    """The rule for a schedule's fields; ValueError(INVALID_SCHEDULE | INVALID_TIMEZONE) when it is not one."""
    if kind == "EVERY_MINUTES":
        return EveryMinutes(int(every_minutes or 0))
    if kind == "DAILY_AT":
        return DailyAt(at or "")
    if kind == "CRON":
        return Cron(cron, tz)
    raise ValueError("INVALID_SCHEDULE")
