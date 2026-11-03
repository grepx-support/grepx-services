# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

from abc import ABC, abstractmethod
from dataclasses import dataclass
from .graph import GraphClient, GraphError

@dataclass
class PublishResult:
    external_id: str
    permalink: str = ""

@dataclass
class Post:
    caption: str
    image_url: str      # public JPEG (Instagram accepts JPEG only)
    link: str           # the event page
    image: bytes = b""  # the same poster, for networks that want the file itself (LinkedIn, Telegram)

class SocialChannel(ABC):
    key = label = icon = setup_hint = ""
    @abstractmethod
    def configured(self) -> bool: ...
    @abstractmethod
    def publish(self, post: Post) -> PublishResult: ...
    @abstractmethod
    def check(self) -> str:
        """Read the account with the saved credentials (nothing is posted); a readable confirmation or GraphError."""

    @staticmethod
    def _cfg(k):
        from .settings import setting
        return setting(k)
    def _graph(self): return GraphClient(self._cfg("META_PAGE_TOKEN"), self._cfg("META_GRAPH_VERSION") or "v25.0")

class FacebookPage(SocialChannel):
    key, label, icon = "facebook", "Facebook Page", "thumbs-up"
    setup_hint = "Integrations → Facebook Page"
    def configured(self): return bool(self._cfg("META_PAGE_ID") and self._cfg("META_PAGE_TOKEN"))
    def publish(self, post):
        page, g = self._cfg("META_PAGE_ID"), self._graph()
        r = g.post(f"{page}/photos", url=post.image_url, caption=f"{post.caption}\n\n{post.link}")
        pid = r.get("post_id") or r.get("id")
        link = g.get(pid, fields="permalink_url").get("permalink_url", "") if pid else ""
        return PublishResult(pid, link)

    def check(self): return "Connected to Page “" + self._graph().get(self._cfg("META_PAGE_ID"), fields="name")["name"] + "”"

class InstagramBusiness(SocialChannel):
    """Two steps, as Instagram requires: create a media container from the image URL, then publish it."""
    key, label, icon = "instagram", "Instagram", "camera"
    setup_hint = "Integrations → Instagram"
    def configured(self): return bool(self._cfg("META_IG_USER_ID") and self._cfg("META_PAGE_TOKEN"))
    def publish(self, post):
        ig, g = self._cfg("META_IG_USER_ID"), self._graph()
        container = g.post(f"{ig}/media", image_url=post.image_url, caption=f"{post.caption}\n\nBook a time: {post.link} (link in bio)")["id"]
        mid = g.post(f"{ig}/media_publish", creation_id=container)["id"]
        return PublishResult(mid, g.get(mid, fields="permalink").get("permalink", ""))

    def check(self): return "Connected to Instagram @" + self._graph().get(self._cfg("META_IG_USER_ID"), fields="username")["username"]

class LinkedInPage(SocialChannel):
    """Company page post with the poster image (needs the Community Management API and w_organization_social)."""
    key, label, icon = "linkedin", "LinkedIn", "briefcase-business"
    setup_hint = "Integrations → LinkedIn page"
    def configured(self): return bool(self._cfg("LINKEDIN_ORG_ID") and self._cfg("LINKEDIN_TOKEN"))
    def publish(self, post):
        from .linkedin import LinkedInClient
        li = LinkedInClient(self._cfg("LINKEDIN_TOKEN"), self._cfg("LINKEDIN_VERSION") or "202608")
        owner = f"urn:li:organization:{self._cfg('LINKEDIN_ORG_ID')}"
        image = li.upload_image(owner, post.image) if post.image else None
        urn = li.post(owner, f"{post.caption}\n\n{post.link}", image)
        return PublishResult(urn, f"https://www.linkedin.com/feed/update/{urn}/" if urn else "")

    def check(self):
        from .linkedin import LinkedInClient
        org = LinkedInClient(self._cfg("LINKEDIN_TOKEN"), self._cfg("LINKEDIN_VERSION") or "202608").organization(self._cfg("LINKEDIN_ORG_ID"))
        return "Connected to LinkedIn page “" + (org.get("localizedName") or self._cfg("LINKEDIN_ORG_ID")) + "”"

class XAccount(SocialChannel):
    """X (Twitter): text + link; X shows the event poster as a preview card from the page's link-preview tags."""
    key, label, icon = "x", "X (Twitter)", "at-sign"
    setup_hint = "Integrations → X (Twitter)"
    def configured(self): return bool(self._cfg("X_ACCESS_TOKEN"))
    def publish(self, post):
        import requests
        text = post.caption.split("\n\n")[0][:230] + f"\n\n{post.link}"
        try: r = requests.post("https://api.x.com/2/tweets", json={"text": text}, timeout=30,
                               headers={"Authorization": f"Bearer {self._cfg('X_ACCESS_TOKEN')}"})
        except requests.RequestException as e: raise GraphError(f"Could not reach X: {e}")
        body = r.json() if r.content else {}
        if r.status_code >= 400: raise GraphError(body.get("detail") or body.get("title") or f"X answered {r.status_code}")
        tid = body["data"]["id"]
        return PublishResult(tid, f"https://x.com/i/web/status/{tid}")

    def check(self):
        import requests
        try: r = requests.get("https://api.x.com/2/users/me", timeout=15, headers={"Authorization": f"Bearer {self._cfg('X_ACCESS_TOKEN')}"})
        except requests.RequestException as e: raise GraphError(f"Could not reach X: {e}")
        body = r.json() if r.content else {}
        if r.status_code >= 400: raise GraphError(body.get("detail") or body.get("title") or f"X answered {r.status_code}")
        return "Connected to X as @" + body["data"]["username"]

class TelegramChannel(SocialChannel):
    """A Telegram channel or group: the bot posts the poster with the caption (bot must be an admin there)."""
    key, label, icon = "telegram", "Telegram channel", "send"
    setup_hint = "Integrations → Telegram channel"
    def configured(self): return bool(self._cfg("TELEGRAM_BOT_TOKEN") and self._cfg("TELEGRAM_CHAT_ID"))
    def publish(self, post):
        import requests
        chat = self._cfg("TELEGRAM_CHAT_ID")
        try: r = requests.post(f"https://api.telegram.org/bot{self._cfg('TELEGRAM_BOT_TOKEN')}/sendPhoto", timeout=30,
                               data={"chat_id": chat, "caption": f"{post.caption}\n\n{post.link}"[:1024]},
                               files={"photo": ("poster.jpg", post.image, "image/jpeg")} if post.image else None)
        except requests.RequestException as e: raise GraphError(f"Could not reach Telegram: {e}")
        body = r.json()
        if not body.get("ok"): raise GraphError(body.get("description") or f"Telegram answered {r.status_code}")
        mid = body["result"]["message_id"]
        link = f"https://t.me/{chat.lstrip('@')}/{mid}" if str(chat).startswith("@") else ""
        return PublishResult(str(mid), link)

    def check(self):
        import requests
        try: r = requests.get(f"https://api.telegram.org/bot{self._cfg('TELEGRAM_BOT_TOKEN')}/getChat", timeout=15,
                              params={"chat_id": self._cfg("TELEGRAM_CHAT_ID")})
        except requests.RequestException as e: raise GraphError(f"Could not reach Telegram: {e}")
        body = r.json()
        if not body.get("ok"): raise GraphError(body.get("description") or f"Telegram answered {r.status_code}")
        return "Connected to Telegram “" + (body["result"].get("title") or body["result"].get("username", "")) + "”"

SOCIAL = {}
def register(channel): SOCIAL[channel.key] = channel
for _c in (FacebookPage(), InstagramBusiness(), LinkedInPage(), XAccount(), TelegramChannel()): register(_c)
