
from superdesk.io.registry import registered_feed_parsers
from .ap_parser import CP_APMediaFeedParser

registered_feed_parsers[CP_APMediaFeedParser.NAME] = CP_APMediaFeedParser()
