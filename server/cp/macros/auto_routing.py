# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

import cp
import re
import logging
import superdesk
from flask_babel import lazy_gettext


logger = logging.getLogger(__name__)


def find_name_item(cv_id, name):
    cv = superdesk.get_resource_service("vocabularies").find_one(req=None, _id=cv_id)
    if not cv or not cv.get("items"):
        return
    for item in cv["items"]:
        if item.get("name").lower() == name:
            return item


def callback(item, **kwargs):
    """ This macro will set the language of the articles to the Desk language. """
    rule = kwargs.get("rule")
    item["profile"] = "autorouting"
    if rule and ":" in rule["name"]:
        service, destination = re.sub(r"\([A-Z]+\)", "", rule["name"]).split(":")
        mapping = {
            cp.DISTRIBUTION: service.strip(),
            cp.DESTINATIONS: destination.strip(),
        }

        for cv_id, name in mapping.items():
            subject = find_name_item(cv_id, name.lower())
            if subject:
                item.setdefault("subject", []).append(
                    {
                        "name": subject["name"],
                        "qcode": subject["qcode"],
                        "scheme": cv_id,
                        "translations": subject.get("translations")
                    }
                )
            else:
                logger.error("no item found in vocabulary %s with name %s", cv_id, name)

        # remove associations for Broadcast content
        if cp.is_broadcast(item) and item.get("associations"):
            item["associations"] = {key: None for key in item["associations"]}

    return item


name = "auto-routing"
label = lazy_gettext("AutoRouting macro")
access_type = "backend"
action_type = "direct"
