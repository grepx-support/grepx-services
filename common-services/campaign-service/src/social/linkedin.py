# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""LinkedIn company page: upload the poster image, then create a post (Posts API, versioned REST)."""
import time
import requests
from .graph import GraphError

class LinkedInClient:
    BASE = "https://api.linkedin.com/rest"

    def __init__(self, token, version, timeout=30):
        self.h = {"Authorization": f"Bearer {token}", "LinkedIn-Version": version, "X-Restli-Protocol-Version": "2.0.0"}
        self.timeout = timeout

    def _req(self, method, url, **kw):
        try: r = requests.request(method, url, headers={**self.h, **kw.pop("headers", {})}, timeout=self.timeout, **kw)
        except requests.RequestException as e: raise GraphError(f"Could not reach LinkedIn: {e}")
        if r.status_code >= 400:
            try: msg = r.json().get("message")
            except ValueError: msg = None
            raise GraphError(msg or f"LinkedIn answered {r.status_code}")
        return r

    def organization(self, org_id):
        return self._req("get", f"{self.BASE}/organizations/{org_id}").json()

    def upload_image(self, owner, data):
        init = self._req("post", f"{self.BASE}/images?action=initializeUpload", json={"initializeUploadRequest": {"owner": owner}}).json()["value"]
        self._req("put", init["uploadUrl"], data=data, headers={"Content-Type": "application/octet-stream"})
        urn = init["image"]
        for _ in range(10):  # LinkedIn processes the image for a moment before it can be used
            status = self._req("get", f"{self.BASE}/images/{requests.utils.quote(urn, safe='')}").json().get("status")
            if status == "AVAILABLE": break
            if status == "PROCESSING_FAILED": raise GraphError("LinkedIn could not process the poster image.")
            time.sleep(1)
        return urn

    def post(self, author, text, image_urn=None):
        body = {"author": author, "commentary": text, "visibility": "PUBLIC", "lifecycleState": "PUBLISHED",
                "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
                "isReshareDisabledByAuthor": False}
        if image_urn: body["content"] = {"media": {"id": image_urn}}
        r = self._req("post", f"{self.BASE}/posts", json=body)
        return r.headers.get("x-restli-id", "")
