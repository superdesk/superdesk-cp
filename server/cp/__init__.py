import logging

# setup cp logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

TZ = "America/Toronto"

ORIG_ID = "itemid"
HEADLINE2 = "headline_extended"
SERVICE = "_service"
FILENAME = "filename"
XMP_KEYWORDS = "xmp_keywords"
CAPTION_WRITER = "caption_writer"
PHOTOGRAPHER_CODE = "photographer_code"
INFOSOURCE = "infosource"
ARCHIVE_SOURCE = "archive_source"
UPDATE = "update"
CORRECTION = "correction"
DISTRIBUTION = "distribution"
DESTINATIONS = "destinations"
BROADCAST = "Broadcast"
ORGANISATION = "organisation"

SLUG_LEN = 32

PHOTO_CATEGORIES = "photo_categories"
PHOTO_SUPPCATEGORIES = "photo_supplementalcategories"

NEWS_URGENT = 1
NEWS_NEED_TO_KNOW = 2
NEWS_GOOD_TO_KNOW = 3
NEWS_BUZZ = 4
NEWS_OPTIONAL = 5
NEWS_FEATURE_REGULAR = 6
NEWS_FEATURE_PREMIUM = 7
NEWS_ROUTINE = 8


def is_broadcast(item):
    try:
        return any(
            [
                s
                for s in item["subject"]
                if s.get("scheme") == DISTRIBUTION and s.get("qcode") == BROADCAST
            ]
        )
    except KeyError:
        return False
