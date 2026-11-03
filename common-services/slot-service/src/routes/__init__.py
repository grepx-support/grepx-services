"""Action routing for slot-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import SlotAction
from . import generate
from . import set_capacity
from . import set_all

TABLE = "slot_requests"
ROUTES = {
    SlotAction.GENERATE: generate.handle,
    SlotAction.SET_CAPACITY: set_capacity.handle,
    SlotAction.SET_ALL: set_all.handle,
}
handle = ActionDispatcher(ROUTES, SlotAction, TABLE)
