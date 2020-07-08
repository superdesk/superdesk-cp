import logging

# setup cp logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

HEADLINE2 = 'headline_extended'
SERVICE = '_service'

NEWS_URGENT = 1
NEWS_NEED_TO_KNOW = 2
NEWS_GOOD_TO_KNOW = 3
NEWS_BUZZ = 4
NEWS_OPTIONAL = 5
NEWS_FEATURE_REGULAR = 6
NEWS_FEATURE_PREMIUM = 7
NEWS_ROUTINE = 8
