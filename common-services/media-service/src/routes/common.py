"""Storage collaborator (swappable in tests)."""
from grepx_storage import Storage, storage_from_env


class Deps:
    storage: Storage | None = None

    @classmethod
    def store(cls) -> Storage:
        if cls.storage is None:
            cls.storage = storage_from_env()
        return cls.storage
