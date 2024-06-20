import logging
import itertools

from planning.feed_parsers.onclusive import OnclusiveFeedParser
from typing import List
from superdesk import get_resource_service

logger = logging.getLogger(__name__)


def unique(values):
    return [
        dict(i)
        for i, _ in itertools.groupby(
            sorted(values, key=lambda k: k["qcode"] + (k.get("scheme") or ""))
        )
    ]


def item_value(subject):
    return {
        k: v
        for k, v in subject.items()
        if k in ("scheme", "name", "qcode", "translations")
    }


class CPOnclusiveFeedParser(OnclusiveFeedParser):
    """
    Superdesk -CP event parser

    Feed Parser which can parse the Onclusive API Events
    """

    _cv_items = {}

    def _get_cv_items(self, _id: str) -> List:
        if _id not in self._cv_items:
            self._cv_items[_id] = get_resource_service("vocabularies").get_items(
                _id=_id, is_active=True
            )
        return self._cv_items[_id]

    def parse(self, content, provider=None):
        onclusive_categories = self._get_cv_items("onclusive_ingest_categories")
        onclusive_event_types = self._get_cv_items("onclusive_event_types")
        cp_categories = self._get_cv_items("categories")
        cp_event_types = self._get_cv_items("event_types")
        subjects = self._get_cv_items("subject_custom")

        items = super().parse(content, provider)
        events = []

        for item in items:
            category = []
            if item.get("subject"):
                for subject in item["subject"]:
                    if subject["scheme"] == "onclusive_categories":
                        onclusive_category = self.find_cv_item(
                            onclusive_categories, subject["qcode"]
                        )
                        if onclusive_category:
                            cp_category = self.find_cv_item(
                                cp_categories, onclusive_category["cp_category"]
                            )
                            if cp_category:
                                category.append(
                                    {
                                        "name": cp_category["name"],
                                        "qcode": cp_category["qcode"],
                                        "translations": cp_category["translations"],
                                    }
                                )
                            if onclusive_category.get("cp_index"):
                                subj = self.find_cv_item(
                                    subjects, onclusive_category["cp_index"]
                                )
                            else:
                                subj = create_missing_subject(
                                    "subject_custom", onclusive_category
                                )
                            if subj:
                                item["subject"].append(item_value(subj))

                    if subject["scheme"] == "onclusive_event_types":
                        onclusive_event_type = self.find_cv_item(
                            onclusive_event_types, subject["qcode"]
                        )
                        if onclusive_event_type:
                            if onclusive_event_type.get("cp_type"):
                                cp_event_type = self.find_cv_item(
                                    cp_event_types, onclusive_event_type["cp_type"]
                                )
                                if cp_event_type:
                                    item["subject"].append(item_value(cp_event_type))
                                else:
                                    logger.warning(
                                        "Event type missing for %s",
                                        onclusive_event_type.get("cp_type"),
                                    )
                            else:
                                item["subject"].append(
                                    item_value(
                                        create_missing_subject(
                                            "event_types", onclusive_event_type
                                        )
                                    )
                                )
                # remove duplicates
                item["anpa_category"] = unique(category)
                item["subject"] = unique(item["subject"])
            events.append(item)
        return events

    def find_cv_item(self, cv_items, qcode):
        """
        Find item in the cv.
        """
        for item in cv_items:
            if str(item["qcode"]) == str(qcode):
                return item


def create_missing_subject(scheme: str, vocabulary_item):
    return {
        "name": vocabulary_item["name"],
        "qcode": vocabulary_item["qcode"].zfill(8),
        "scheme": scheme,
        "translations": vocabulary_item.get("translations") or {},
    }
