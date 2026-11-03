"""audit-log-service records every entry; the row's `action` is the audited business action, not a route."""
from grepx_service import ActionDispatcher

from dto import AuditLogAction
from . import record

TABLE = "audit_log"
handle = ActionDispatcher({}, AuditLogAction, TABLE, action_field="route", default=record.handle)
