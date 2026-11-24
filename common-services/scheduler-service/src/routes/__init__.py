# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for scheduler-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import SchedulerAction as A
from . import cancel, pause, register, run_now, views

TABLE = "schedule_requests"
ROUTES = {
    A.REGISTER: register.handle,
    A.CANCEL: cancel.handle,
    A.PAUSE: pause.pause,
    A.RESUME: pause.resume,
    A.RUN_NOW: run_now.handle,
    A.PREVIEW: views.preview,
    A.SCHEDULES: views.schedules,
    A.TICKS: views.ticks,
    A.HEALTH: views.health,
}
handle = ActionDispatcher(ROUTES, A, TABLE)
