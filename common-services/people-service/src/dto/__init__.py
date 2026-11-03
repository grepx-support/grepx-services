# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Single import door for people-service vocabulary."""
from .person_action import PersonAction
from .person_field import PersonField
from .reason_code import ReasonCode

PEOPLE_TABLE = "people"
CONTACT_FIELDS = (PersonField.NAME, PersonField.EMAIL, PersonField.PHONE)

__all__ = ["PersonAction", "PersonField", "ReasonCode", "PEOPLE_TABLE", "CONTACT_FIELDS"]
