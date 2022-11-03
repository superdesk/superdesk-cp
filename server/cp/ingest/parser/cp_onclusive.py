import itertools
from planning.feed_parsers.onclusive import OnclusiveFeedParser
from typing import List
from superdesk import get_resource_service


class CPOnclusiveFeedParser(OnclusiveFeedParser):
    """
    Superdesk -CP event parser

    Feed Parser which can parse the Onclusive API Events
    """

    _cv_items = {}

    def _get_cv_items(self, _id: str) -> List:
        if _id not in self._cv_items:
            self._cv_items[_id] = get_resource_service("vocabularies").get_items(_id=_id, is_active=True)
        return self._cv_items[_id]

    def parse(self, content, provider=None):
        onclusive_cv_items = self._get_cv_items("onclusive_ingest_categories")
        anpa_categories = self._get_cv_items("categories")
        event_types = self._get_cv_items("event_types")
        onclusive_event_types = self._get_cv_items("onclusive_event_types")

        items = super().parse(content, provider)
        events = []

        for item in items:
            category = []
            all_event_types = []
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
                        onclusive_event_type = self.find_cv_item(
                            onclusive_event_types, subject["name"]
                        )
                        if onclusive_event_type:
                            cp_event = self.parse_event_type(
                                onclusive_event_type["cp_type"],
                                event_types,
                                all_event_types,
                            )
                            if cp_event:
                                item["subject"] += cp_event

                # remove duplicates
                item["anpa_category"] = [
                    dict(i)
                    for i, _ in itertools.groupby(
                        sorted(category, key=lambda k: k["qcode"])
                    )
                ]
                item["subject"] = [
                    dict(i)
                    for i, _ in itertools.groupby(
                        sorted(item["subject"], key=lambda k: k["qcode"])
                    )
                ]
            events.append(item)
        return events

    def find_cv_item(self, cv_items, qcode):
        """
        Find item in the cv.
        """
        for item in cv_items:
            if item["qcode"] == qcode:
                return item

    def parse_event_type(self, qcode, cp_event_types, events: list) -> List:
        """
        Find events types from the CV including it's parent item.
        """
        event_type = self.find_cv_item(cp_event_types, qcode)
        if event_type:
            events.append(
                {
                    "name": event_type["name"],
                    "qcode": event_type["qcode"],
                    "scheme": "event_types",
                }
            )
        if event_type and event_type.get("parent"):
            self.parse_event_type(event_type["parent"], cp_event_types, events)

        return events
