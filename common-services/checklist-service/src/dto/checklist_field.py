# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Fields of checklist requests and templates."""
from enum import Enum


class ChecklistField(str, Enum):
    TEMPLATE_KEY = "template_key"
    NAME = "name"
    ITEMS = "items"
    REF_TYPE = "ref_type"
    REF_ID = "ref_id"
    REF_LABEL = "ref_label"
    BASE_DATE = "base_date"
    ONLY_OPEN = "only_open"
    ACTOR_ID = "actor_id"
    TENANT_ID = "tenant_id"
    CREATED = "created"
    REMOVED = "removed"
