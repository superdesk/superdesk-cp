from superdesk.io.registry import registered_feed_parsers, register_feed_parser

from .parser.ap import CP_APMediaFeedParser
from .parser.businesswire import BusinessWireParser
from .parser.globenewswire import GlobeNewswireParser
#from .parser.cp_onclusive import CPOnclusiveFeedParser


def init_app(app):
    # register new parsers
    register_feed_parser(BusinessWireParser.NAME, BusinessWireParser())
    register_feed_parser(GlobeNewswireParser.NAME, GlobeNewswireParser())

    # override core parsers
    registered_feed_parsers[CP_APMediaFeedParser.NAME] = CP_APMediaFeedParser()

    # override planning parser
    #registered_feed_parsers[CPOnclusiveFeedParser.NAME] = CPOnclusiveFeedParser()
