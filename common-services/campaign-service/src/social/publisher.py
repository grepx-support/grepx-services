# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

from .channels import SOCIAL, Post
from .graph import GraphError

class SocialPublisher:
    """Posts one event to the chosen networks; the caller records every attempt (success or the network's error)."""
    def __init__(self, repo, channels=None): self.repo, self.channels = repo, channels or SOCIAL

    def publish(self, event, networks, caption, image_url, link, user_id=None, image=b""):
        results = {}
        for key in networks:
            ch = self.channels.get(key)
            if not ch: continue
            if not ch.configured():
                results[key] = (False, f"{ch.label} is not set up ({ch.setup_hint}).")
                self.repo.add(event["id"], key, "failed", None, "", results[key][1], caption, user_id); continue
            try:
                r = ch.publish(Post(caption, image_url, link, image))
                self.repo.add(event["id"], key, "posted", r.external_id, r.permalink, None, caption, user_id)
                results[key] = (True, r.permalink)
            except (GraphError, KeyError) as e:
                self.repo.add(event["id"], key, "failed", None, "", str(e), caption, user_id)
                results[key] = (False, str(e))
        return results
