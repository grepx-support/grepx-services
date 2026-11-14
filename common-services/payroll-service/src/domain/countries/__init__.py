# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The countries payroll knows. Add a country = one small file with a Country subclass, listed here."""
from .australia import Australia
from .base import Country, bracket_tax, line
from .india import India
from .singapore import Singapore

COUNTRIES = {c.code: c for c in (Country(), India(), Australia(), Singapore())}

__all__ = ["COUNTRIES", "Country", "bracket_tax", "line"]
