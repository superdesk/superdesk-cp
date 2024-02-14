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
from superdesk.metadata.item import CONTENT_STATE


logger = logging.getLogger(__name__)


def find_name_item(cv_id, name):
    cv = superdesk.get_resource_service("vocabularies").find_one(req=None, _id=cv_id)
    if not cv or not cv.get("items"):
        return
    for item in cv["items"]:
        if item.get("name").lower() == name:
            return item


def callback(item, **kwargs):
    """This macro will set the language of the articles to the Desk language."""
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
                        "translations": subject.get("translations"),
                    }
                )
            else:
                logger.error("no item found in vocabulary %s with name %s", cv_id, name)

        # handle APR specific output
        if cp.is_broadcast(item):
            if item.get("associations"):
                item["associations"] = {key: None for key in item["associations"]}
            if item.get("abstract"):
                item["body_html"] = item.pop("abstract")

    manually_edited = (
        superdesk.get_resource_service("archive")
        .find(
            where={
                "$and": [
                    {"uri": item["uri"]},
                    # can't use $nin, looks like bug in eve
                    # converting [None, ""] to [ObjectId(), ""]
                    {"version_creator": {"$ne": None}},
                    {"version_creator": {"$ne": ""}},
                    {"state": {"$ne": CONTENT_STATE.SPIKED}},
                ],
            },  # type: ignore
            max_results=1,
        )
        .sort("versioncreated", -1)
    )

    if manually_edited.count():
        logger.info("Manually updated before %s", item["slugline"])
        prev = manually_edited[0]
        subj = [
            subject
            for subject in prev["subject"]
            if subject.get("scheme") == cp.AP_INGEST_CONTROL
        ]
        if subj and subj[0]["qcode"] == "stop":
            logger.info("Stop auto publish %s", item["slugline"])
            item["auto_publish"] = False  # stop auto publishing
        elif subj and subj[0]["qcode"] == "ranking" and prev.get("urgency"):
            logger.info("Update ranking %s", item["slugline"])
            item["urgency"] = prev["urgency"]
        else:
            logger.info("Auto publish previously edited %s", item["slugline"])

    return item


name = "auto-routing"
label = lazy_gettext("AutoRouting macro")
access_type = "backend"
action_type = "direct"
