# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Storage collaborator (swappable in tests)."""
from grepx_storage import Storage, storage_from_env


class Deps:
    storage: Storage | None = None

    @classmethod
    def store(cls) -> Storage:
        if cls.storage is None:
            cls.storage = storage_from_env()
        return cls.storage
