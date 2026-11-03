"""Action routing for media-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import MediaAction
from . import process
from . import delete

TABLE = "media_requests"
ROUTES = {
    MediaAction.PROCESS: process.handle,
    MediaAction.DELETE: delete.handle,
}
handle = ActionDispatcher(ROUTES, MediaAction, TABLE)
