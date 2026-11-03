<!--
  Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
  This file is part of the GrepX platform and is proprietary and confidential.
  Unauthorised copying, use, modification or distribution is strictly prohibited.
-->

# grepx-services

The generic GrepX services, released together. Each one owns its tables, takes request rows through Nexus, and reads
product specifics (person table, message templates per role, links, checklist, points) from the workspace's deployment
file and product rules from plugins - so every product reuses them unchanged.

identity (auth, access) · notification · template · scheduler · task · checklist · audit-log · media · settings ·
people · event · slot · booking · campaign · recognition · referral · event-report · questionnaire

Run inside a product workspace: the product repo's `./workspace.sh` links `common-services/` from here.
Each service: `src/` (dto, domain, routes, jobs), `config/config.yaml`, `test/`, and `setup.sh` / `run.sh` wrappers.
Gate: `platform/tools/test/test_second_product.py` (in grepx-platform) runs a new product on these services alone.
