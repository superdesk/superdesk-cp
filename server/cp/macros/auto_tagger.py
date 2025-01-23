from flask_babel import lazy_gettext
from flask import current_app as app
from cp.ai.semaphore import Semaphore

import logging

logger = logging.getLogger(__name__)


def qcode(value):
    return "{}:{}".format(value.get("scheme"), value.get("qcode"))


def update_tag_relevance(existing_tag, new_tag):
    """Update the relevance of an existing tag with the new tag's relevance."""
    if "relevance" in new_tag and new_tag["relevance"] is not None:
        existing_tag["relevance"] = new_tag["relevance"]


def callback(item, **kwargs):
    """This macro will tag the item using the AutoTagging service based on the item's content."""
    semaphore = Semaphore(app)
    tags = semaphore.analyze(item)

    if tags:
        for key, values in tags.items():
            item.setdefault(key, [])
            for new_value in values:
                existing_tag = next(
                    (tag for tag in item[key] if qcode(tag) == qcode(new_value)), None
                )
                if existing_tag:
                    update_tag_relevance(existing_tag, new_value)
                else:
                    item[key].append(new_value)

    return item


name = "auto-tagger"
label = lazy_gettext("Auto Tagger")
access_type = "backend"
action_type = "direct"
