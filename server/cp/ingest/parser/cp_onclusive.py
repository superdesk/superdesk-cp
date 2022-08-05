import itertools
from planning.feed_parsers.onclusive import OnclusiveFeedParser
from typing import List
from superdesk import get_resource_service


def _get_cv_items(_id: str) -> List:
    cv = get_resource_service("vocabularies").find_one(req=None, _id=_id)
    return cv["items"]


class CPOnclusiveFeedParser(OnclusiveFeedParser):
    """
    Superdesk -CP event parser

    Feed Parser which can parse the Onclusive API Events
    """

    event = []

    def parse(self, content, provider=None):
        onclusive_cv_items = _get_cv_items("onclusive_ingest_categories")
        anpa_categories = _get_cv_items("categories")
        event_types = _get_cv_items("event_types")
        cp_event_types = _get_cv_items("cp_event_types")

        items = super().parse(content, provider)

        for item in items:
            category = []
            eventType = []
            if item.get("subject"):
                for subject in item.get("subject"):
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
                    if subject["scheme"] == "onclusive_event_types":
                        cp_event_type = self.find_cv_item(
                            cp_event_types, subject["name"].lower()
                        )
                        if cp_event_type and cp_event_type.get("is_active"):
                            event_type = self.find_cv_item(
                                event_types, cp_event_type["cp_type"]
                            )
                            if event_type and event_type.get("is_active"):
                                eventType.append(
                                    {
                                        "name": event_type["name"],
                                        "qcode": event_type["qcode"],
                                        "scheme": "event_types",
                                    }
                                )
                # remove duplicates
                item["anpa_category"] = [
                    dict(i)
                    for i, _ in itertools.groupby(
                        sorted(category, key=lambda k: k["qcode"])
                    )
                ]
                item["subject"] += [
                    dict(i)
                    for i, _ in itertools.groupby(
                        sorted(eventType, key=lambda k: k["qcode"])
                    )
                ]
            self.event.append(item)
        return self.event

    def find_cv_item(self, cv_items, qcode):
        """
        Find item in the cv.
        """
        for item in cv_items:
            if item["qcode"] == qcode:
                return item
