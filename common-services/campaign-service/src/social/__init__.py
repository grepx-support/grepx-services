# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

"""Publish events to social media: Facebook Page and Instagram (Meta Graph API), LinkedIn page, X, Telegram channel.

Adding another network = one Channel subclass + register() (Strategy + Registry, like messaging/channels.py)."""
from .channels import SOCIAL, SocialChannel, PublishResult
from .publisher import SocialPublisher

__all__ = ["SOCIAL", "SocialChannel", "PublishResult", "SocialPublisher"]
