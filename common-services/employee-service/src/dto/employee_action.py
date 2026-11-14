# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Actions employee-service accepts."""
from enum import Enum


class EmployeeAction(str, Enum):
    SAVE = "SAVE"                        # add or change an employee (profile, position, sites, pay basis)
    SET_DOCUMENT = "SET_DOCUMENT"        # add or change one document (licence, visa, ID, certificate) with its expiry
    REMOVE_DOCUMENT = "REMOVE_DOCUMENT"
    END = "END"                          # the employee leaves: last day and reason; the record stays
    TEAM = "TEAM"                        # the list (one site or all) and the documents needing action
