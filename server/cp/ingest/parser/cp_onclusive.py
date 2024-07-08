import itertools
from planning.feed_parsers.onclusive import OnclusiveFeedParser
from typing import List
from superdesk import get_resource_service
from flask import g


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
        if k not in ("onclusive_ids", "subject", "is_active")
    }


class CPOnclusiveFeedParser(OnclusiveFeedParser):
    """
    Superdesk -CP event parser

    Feed Parser which can parse the Onclusive API Events
    """

    def _get_cv_items(self, _id: str) -> List:
        if "cache" not in g:
            g.cache = {}
        assert isinstance(g.cache, dict)
        cache_id = f"{_id}_cv_items"
        if cache_id not in g.cache:
            g.cache[cache_id] = get_resource_service("vocabularies").get_items(
                _id=_id, is_active=True
            )
        return g.cache[cache_id]

    def parse(self, content, provider=None):
        onclusive_cv_items = self._get_cv_items("onclusive_ingest_categories")
        anpa_categories = self._get_cv_items("categories")
        event_types = self._get_cv_items("event_types")
        subjects = self._get_cv_items("subject_custom")

        items = super().parse(content, provider)
        events = []

        for item in items:
            category = []
            if item.get("subject"):
                for subject in item["subject"]:
                    if subject["scheme"] == "onclusive_categories":
                        onclusive_category = self.find_cv_item(
                            onclusive_cv_items, subject["qcode"]
                        )
                        if onclusive_category:
                            anpa_category = self.find_cv_item(
                                anpa_categories, onclusive_category["cp_category"]
                            )
                            if anpa_category:
                                category.append(
                                    {
                                        "name": anpa_category["name"],
                                        "qcode": anpa_category["qcode"],
                                        "translations": anpa_category["translations"],
                                    }
                                )
                            if onclusive_category.get("cp_index"):
                                subj = self.find_cv_item(
                                    subjects, onclusive_category["cp_index"]
                                )
                            else:
                                subj = {
                                    "name": onclusive_category["name"],
                                    "qcode": onclusive_category["qcode"].zfill(8),
                                    "scheme": "subject_custom",
                                    "translations": onclusive_category.get(
                                        "translations"
                                    ),
                                }
                            if subj:
                                item["subject"].append(item_value(subj))
                    if subject["scheme"] == "onclusive_event_types":
                        event_type = self.find_cv_item(event_types, subject["qcode"])
                        if event_type:
                            item["subject"].append(item_value(event_type))
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
            if item["qcode"] == qcode:
                return item
