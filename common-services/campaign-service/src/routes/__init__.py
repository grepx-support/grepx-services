"""Action routing for campaign-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import CampaignAction
from . import announce
from . import invite
from . import broadcast
from . import publish_social
from . import test_social

TABLE = "campaign_requests"
ROUTES = {
    CampaignAction.ANNOUNCE: announce.handle,
    CampaignAction.INVITE: invite.handle,
    CampaignAction.BROADCAST: broadcast.handle,
    CampaignAction.PUBLISH_SOCIAL: publish_social.handle,
    CampaignAction.TEST_SOCIAL: test_social.handle,
}
handle = ActionDispatcher(ROUTES, CampaignAction, TABLE)
