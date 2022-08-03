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

from flask import current_app as app
from flask_babel import lazy_gettext
from superdesk import get_resource_service
from eve.utils import ParsedRequest
from apps.archive.common import format_dateline_to_locmmmddsrc
from superdesk.geonames import geonames_request, format_geoname_item


logger = logging.getLogger(__name__)

destination_qcodes = ["sfstf", "apfra", "cpstf", "ap---"]


def set_dateline(item, dateline):
    located = item.get("dateline", {}).get("located")

    if located:
        if located.get("place") and dateline:
            located["place"] = dateline

        if located.get("city") and dateline.get("name"):
            located["city"] = dateline["name"]

        # We use the name here because we don't have the city code in the Geonames API.
        if located.get("city_code") and dateline.get("name"):
            located["city_code"] = dateline["name"]

        if located.get("country") and dateline.get("country"):
            located["country"] = dateline["country"]

        if located.get("state") and dateline.get("state"):
            located["state"] = dateline["state"]

        if item.get("dateline", {}).get("text"):
            item["dateline"]["text"] = format_dateline_to_locmmmddsrc(
                located, item["dateline"]["date"]
            )

    return item


def get_destination(items, qcode):
    for item in items:
        if item.get("qcode", "") == qcode:
            return item


def set_dateline_for_translation(item):
    """Set dateline fields required while translation using geoname API"""
    located = item.get("dateline", {}).get("located")
    if located and not located.get("place"):
        try:
            # required params for geoname API
            params = [
                ("name", located.get("city", "")),
                ("lang", item.get("language", "en")),
                ("style", app.config.get("GEONAMES_SEARCH_STYLE", "full")),
            ]
            for feature_class in app.config.get("GEONAMES_FEATURE_CLASSES", ["P"]):
                params.append(("featureClass", feature_class.upper()))

            # get geo data from geoname_request
            json_data = geonames_request("search", params)

            formatted_geoname_item = None
            for item_ in json_data.get("geonames", []):
                if (
                    float(item_["lat"]) == located["location"]["lat"]
                    and float(item_["lng"]) == located["location"]["lon"]
                ):
                    formatted_geoname_item = format_geoname_item(item_)
                    break

            if formatted_geoname_item:
                item["dateline"]["located"].update(
                    {
                        "state_code": formatted_geoname_item["state_code"],
                        "tz": formatted_geoname_item["tz"],
                        "country_code": formatted_geoname_item["country_code"],
                        "state": formatted_geoname_item["state"],
                        "country": formatted_geoname_item["country"],
                        "code": formatted_geoname_item["code"],
                        "scheme": formatted_geoname_item["scheme"],
                        "location": formatted_geoname_item["location"],
                    }
                )
                # set place key required while translation
                item["dateline"]["located"]["place"] = formatted_geoname_item

        except Exception as e:
            logger.exception(
                "Unable to translate dateline for {} item: {}".format(
                    item["guid"], str(e)
                )
            )
            pass


def update_translation_metadata_macro(item, **kwargs):
    req = ParsedRequest()
    req.args = {}

    set_dateline_for_translation(item)

    located = item.get("dateline", {}).get("located")
    if located and located.get("place"):
        dateline = get_resource_service("places_autocomplete").get_place(
            located["place"]["code"], "fr"
        )
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

    # Check if destination is present.
    destination_present = any(
        subject for subject in subjects if subject.get("scheme") == "destinations"
    )

    destinations = [
        cv_item for cv_item in cv["items"] if cv_item.get("qcode") in destination_qcodes
    ]

    # If subjects are present override them else add a new subject
    if subjects and destination_present:
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

        subjects.append(
            {
                "name": destination["name"],
                "qcode": destination["qcode"],
                "scheme": "destinations",
            }
        )

    item["subject"] = subjects

    return item


name = "Update translation metadata macro"
label = lazy_gettext("Update translation metadata macro")
callback = update_translation_metadata_macro
access_type = "backend"
action_type = "interactive"
