"""CredentialRepository — auth-service's private store (password hashes never touch the bus).

Backed by grepx_store, so the database (SQLite, PostgreSQL, MongoDB) is chosen in config, not here.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional

from grepx_store import DocumentStore, MemoryStore

COLLECTION = "credentials"


@dataclass
class Credential:
    user_id: str
    email: str
    password_hash: str
    tenant_id: str
    reset_requested_at: float = 0.0
    external: dict = field(default_factory=dict)   # provider -> subject (e.g. {"google": "1234…"})


class CredentialRepository:
    def __init__(self, store: Optional[DocumentStore] = None):
        self.store = store or MemoryStore()

    def by_email(self, email: str) -> Optional[Credential]:
        found = self.store.find(COLLECTION, email=email.strip().lower())
        return Credential(**found[0]) if found else None

    def by_id(self, user_id: str) -> Optional[Credential]:
        doc = self.store.get(COLLECTION, user_id)
        return Credential(**doc) if doc else None

    def save(self, cred: Credential) -> None:
        """One credential per email: an older one for the same email (left behind when the people records were
        reset but this database was kept) is removed, so login never finds a stale password first."""
        cred.email = cred.email.strip().lower()
        for old in self.store.find(COLLECTION, email=cred.email):
            if old["user_id"] != cred.user_id:
                self.store.delete(COLLECTION, old["user_id"])
        self.store.put(COLLECTION, cred.user_id, asdict(cred))
