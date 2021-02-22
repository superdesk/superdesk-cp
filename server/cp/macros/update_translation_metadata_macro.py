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
from eve.utils import ParsedRequest
from apps.archive.common import format_dateline_to_locmmmddsrc


logger = logging.getLogger(__name__)

destination_qcodes = ["sfstf", "apfra", "cpstf", "ap---"]


def set_dateline(item, dateline):
    located = item.get("dateline", {}).get("located")

    if located:
        if located.get("place") and dateline:
            located["place"] = dateline

        if located.get("city") and dateline.get("name"):
            located["city"] = dateline["name"]

        if located.get("city_code") and dateline.get("name"):
            located["city_code"] = dateline["name"]

        if located.get("country") and dateline.get("country"):
            located["country"] = dateline["country"]

        if located.get("state") and dateline.get("state"):
            located["state"] = dateline["state"]

        if item.get("dateline", {}).get("text"):
            item["dateline"]["text"] = format_dateline_to_locmmmddsrc(located, item["dateline"]["date"])

    return item


def get_destination(items, qcode):
    for item in items:
        if item.get("qcode", "") == qcode:
            return item


def update_translation_metadata_macro(item, **kwargs):
    req = ParsedRequest()
    req.args = {}

    located = item.get("dateline", {}).get("located")

    if located.get("place"):
        req.args["geonameId"] = located["place"].get("code")
        req.args["lang"] = "fr"
        dateline = get_resource_service("places_autocomplete").get_detail(req=req, lookup=None)
        item = set_dateline(item, dateline)

    if item.get("anpa_take_key"):
        item["anpa_take_key"] = ""

    if item.get("correction_sequence"):
        item["correction_sequence"] = 0

    cv = get_resource_service("vocabularies").find_one(req=None, _id="destinations")
    if not cv or not cv.get("items"):
        return

    subjects = item.get("subject", [])

    # Remove out all the fields which are of no use.
    subjects = [
        sub
        for sub in subjects
        if (
            (
                sub.get("qcode") in destination_qcodes
                and sub.get("scheme") == "destinations"
            )
            or sub.get("scheme") != "destinations"
        )
    ]

    destinations = [
        cv_item for cv_item in cv["items"] if cv_item.get("qcode") in destination_qcodes
    ]

    # If subjects are present override them else add a new subject
    if subjects:
        for subject in subjects:
            destination = {}
            if subject.get("qcode") == "cpstf":
                destination = get_destination(destinations, "sfstf")

            elif subject.get("qcode") == "ap---":
                destination = get_destination(destinations, "apfra")

            if destination:
                subject.update(
                    {
                        "name": destination.get("name"),
                        "qcode": destination.get("qcode"),
                        "scheme": "destinations",
                    }
                )
    else:
        destination = get_destination(destinations, "sfstf")

        subjects = [
            {
                "name": destination["name"],
                "qcode": destination["qcode"],
                "scheme": "destinations",
            }
        ]

    item["subject"] = subjects

    return item


name = "Update translation metadata macro"
label = lazy_gettext("Update translation metadata macro")
callback = update_translation_metadata_macro
access_type = "backend"
action_type = "interactive"
