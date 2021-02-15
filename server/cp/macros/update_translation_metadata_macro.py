# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

import logging
from flask_babel import lazy_gettext
from superdesk import get_resource_service

logger = logging.getLogger(__name__)

override_fields = ["Presse Canadienne staff", "L'Associated Press"]


def get_destination(items, name):
    for item in items:
        if item.get('name').lower() == name.lower():
            return item


def update_translation_metadata_macro(item, **kwargs):
    if item.get("anpa_take_key"):
        item["anpa_take_key"] = ""

    if item.get("correction_sequence"):
        item["correction_sequence"] = 0

    cv = get_resource_service("vocabularies").find_one(req=None, _id="destinations")
    if not cv or not cv.get("items"):
        return

    subjects = item.get("subject", [])
    is_destination_present = any(sub for sub in subjects if sub.get("name") in override_fields)

    destinations = [cv for cv in cv["items"] if cv.get("name") in override_fields]

    for subject in subjects:
        if subject.get("name") == "Canadian Press Staff" and not is_destination_present:
            destination = get_destination(destinations, "Presse Canadienne staff")

            subject.update({
                "name": destination.get("name"),
                "qcode": destination.get("qcode"),
                "scheme": "destinations",
            })
        elif subject.get("name") == "The Associated Press" and not is_destination_present:
            destination = get_destination(destinations, "L'Associated Press")

            subject.update({
                "name": destination.get("name"),
                "qcode": destination.get("qcode"),
                "scheme": "destinations",
            })
        elif not is_destination_present:
            destination = get_destination(destinations, "Presse Canadienne staff")

            subject.update({
                "name": destination.get("name"),
                "qcode": destination.get("qcode"),
                "scheme": "destinations",
            })

    return item


name = "Update translation metadata macro"
label = lazy_gettext("Update translation metadata macro")
callback = update_translation_metadata_macro
access_type = "backend"
action_type = "interactive"
