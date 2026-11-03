# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

import requests

class GraphError(RuntimeError): pass

class GraphClient:
    """Tiny Meta Graph API client: POST/GET with the page token, Meta's own error text on failure."""
    def __init__(self, token, version="v25.0", timeout=30):
        self.token, self.base, self.timeout = token, f"https://graph.facebook.com/{version}", timeout

    def post(self, path, **data): return self._call("post", path, data=data)
    def get(self, path, **params): return self._call("get", path, params=params)

    def _call(self, method, path, **kw):
        kw.setdefault("data" if method == "post" else "params", {})["access_token"] = self.token
        try: r = getattr(requests, method)(f"{self.base}/{path.lstrip('/')}", timeout=self.timeout, **kw)
        except requests.RequestException as e: raise GraphError(f"Could not reach Facebook: {e}")
        body = r.json() if r.headers.get("content-type", "").startswith(("application/json", "text/javascript")) else {}
        if r.status_code >= 400 or "error" in body:
            raise GraphError((body.get("error") or {}).get("message") or f"Facebook answered {r.status_code}")
        return body
