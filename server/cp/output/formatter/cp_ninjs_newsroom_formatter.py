# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license


import superdesk
import logging
import json

from superdesk.publish.formatters import NewsroomNinjsFormatter

from cp import is_broadcast


logger = logging.getLogger(__name__)


class CPNewsroomNinjsFormatter(NewsroomNinjsFormatter):
    name = "CP Newsroom NINJS"
    type = "cp newsroom ninjs"

    def __init__(self):
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
                name_in_vocab = item.get("name")
                qcode = item.get("qcode")
                # Prepare the translated name, defaulting to the original name if the translation is not available
                translated_name = (
                    item.get("translations", {})
                    .get("name", {})
                    .get(language, name_in_vocab)
                )

                # Always populate vocab_mapping_all
                vocab_mapping_all[name_in_vocab.lower()] = (qcode, translated_name)

                # Only populate vocab_mapping if "in_jimi" is True
                if item.get("in_jimi") is True:
                    vocab_mapping[name_in_vocab.lower()] = (qcode, translated_name)

            updated_subjects = list(ninjs["subject"])
            # Setting a Pre defined Allowed Scheme Vocabulary Mapping

            allowed_schemes = [
                "http://cv.iptc.org/newscodes/mediatopic/",
                "subject_custom",
                "subject",
                "http://cv.cp.org/cp-subject-legacy/",
            ]

            for subject in ninjs["subject"]:
                subject_name = subject.get("name").lower()
                subject_scheme = subject.get("scheme", "")

                if subject_name in vocab_mapping and subject_scheme in allowed_schemes:
                    qcode, translated_name = vocab_mapping[subject_name]
                    updated_subjects.append(
                        {
                            "code": qcode,
                            "name": translated_name,
                            "scheme": "http://cv.cp.org/cp-subject-legacy/",
                        }
                    )
                else:
                    if (
                        subject_name in vocab_mapping_all
                        and subject_scheme in allowed_schemes
                    ):
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
                f"An error occurred. We are in NewsRoom Ninjs Formatter Ninjs Subjects exception: {str(e)}"
            )

    def _transform_to_ninjs(self, article, subscriber, recursive=True):
        ninjs = super()._transform_to_ninjs(article, subscriber, recursive)

        self.update_ninjs_subjects(ninjs, "en-CA")

        if is_broadcast(article) and ninjs["guid"] == article.get("ingest_id"):
            ninjs["guid"] = ninjs["guid"] + "-br"

        return ninjs
