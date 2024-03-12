# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license


from .ninjs_formatter import NINJSFormatter
import superdesk
import elasticapm
import json
import logging

logger = logging.getLogger(__name__)


class NewsroomNinjsFormatter(NINJSFormatter):
    name = "Newsroom NINJS"
    type = "newsroom ninjs"

    def __init__(self):
        self.format_type = "newsroom ninjs"
        self.can_preview = False
        self.can_export = False
        self.internal_renditions = ["original", "viewImage", "baseImage"]

    def update_ninjs_subjects(self, ninjs, language="en-CA"):
        try:

            # Fetch the vocabulary
            cv = superdesk.get_resource_service("vocabularies").find_one(
                req=None, _id="subject_custom"
            )
            vocab_items = cv.get("items", [])
            vocab_mapping = {}

            vocab_mapping_all = {}

            for item in vocab_items:
                if item.get("in_jimi") is True:
                    name_in_vocab = item.get("name")
                    qcode = item.get("qcode")
                    translated_name = (
                        item.get("translations", {})
                        .get("name", {})
                        .get(language, name_in_vocab)
                    )
                    vocab_mapping[name_in_vocab.lower()] = (qcode, translated_name)

            for item in vocab_items:
                name_in_vocab = item.get("name")
                qcode = item.get("qcode")
                translated_name = (
                    item.get("translations", {})
                    .get("name", {})
                    .get(language, name_in_vocab)
                )
                vocab_mapping_all[name_in_vocab.lower()] = (qcode, translated_name)

            updated_subjects = list(ninjs["subject"])

            for subject in ninjs["subject"]:
                subject_name = subject.get("name").lower()
                if subject_name in vocab_mapping:
                    qcode, translated_name = vocab_mapping[subject_name]
                    updated_subjects.append(
                        {
                            "code": qcode,
                            "name": translated_name,
                            "scheme": "http://cv.cp.org/cp-subject-legacy/",
                        }
                    )
                else:
                    if subject_name in vocab_mapping_all:
                        qcode, translated_name = vocab_mapping_all[subject_name]
                        updated_subjects.append(
                            {
                                "code": qcode,
                                "name": translated_name,
                                "scheme": "subject_custom",
                            }
                        )

            ninjs["subject"] = [
                {
                    **subject,
                    "name": (
                        vocab_mapping_all[subject["name"].lower()][1]
                        if subject["name"].lower() in vocab_mapping_all
                        and subject["scheme"] in ["subject"]
                        else subject["name"]
                    ),
                    "scheme": (
                        "subject_custom"
                        if subject.get("scheme")
                        in ["http://cv.iptc.org/newscodes/mediatopic/", "subject"]
                        else subject.get("scheme")
                    ),
                }
                for subject in updated_subjects
            ]

            ninjs["subject"] = list(
                {
                    json.dumps(subject, sort_keys=True): subject
                    for subject in ninjs["subject"]
                }.values()
            )

        except Exception as e:
            logger.error(
                f"An error occurred. We are in NewsRoom Ninjs Formatter Ninjs Subjects exception:  {str(e)}"
            )

    @elasticapm.capture_span()
    def _format_products(self, article):
        """
        Return a list of API product id's that the article matches.

        :param article:
        :return:
        """
        result = superdesk.get_resource_service("product_tests").test_products(article)
        return [
            {"code": p["product_id"], "name": p.get("name")}
            for p in result
            if p.get("matched", False)
        ]

    @elasticapm.capture_span()
    def _transform_to_ninjs(self, article, subscriber, recursive=True):
        ninjs = super()._transform_to_ninjs(article, subscriber, recursive)

        if article.get("ingest_id") and article.get("auto_publish"):
            ninjs["guid"] = article.get("ingest_id")
            if article.get("ingest_version"):
                ninjs["version"] = article["ingest_version"]

        ninjs["products"] = self._format_products(article)

        if article.get("assignment_id"):
            assignment = superdesk.get_resource_service("assignments").find_one(
                req=None, _id=article["assignment_id"]
            )
            if assignment is not None:
                if assignment.get("coverage_item"):
                    ninjs.setdefault("coverage_id", assignment["coverage_item"])
                if assignment.get("planning_item"):
                    ninjs.setdefault("planning_id", assignment["planning_item"])

        if article.get("refs"):
            ninjs["refs"] = article["refs"]

        self.update_ninjs_subjects(ninjs, "en-CA")

        return ninjs
