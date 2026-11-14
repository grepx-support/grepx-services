# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Single import door for employee-service vocabulary."""
from .employee_action import EmployeeAction
from .reason_code import ReasonCode

EMPLOYEES = "employees"

__all__ = ["EmployeeAction", "ReasonCode", "EMPLOYEES"]
