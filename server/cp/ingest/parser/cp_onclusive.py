import itertools
from planning.feed_parsers.onclusive import OnclusiveFeedParser
from typing import List
from superdesk import get_resource_service


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

    _cv_items = {}

    def _get_cv_items(self, _id: str) -> List:
        if _id not in self._cv_items:
            self._cv_items[_id] = get_resource_service("vocabularies").get_items(
                _id=_id, is_active=True
            )
        return self._cv_items[_id]

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
                        event_type = self.find_event_type(event_types, subject["qcode"])
                        if event_type:
                            item["subject"].append(item_value(event_type))
                # remove duplicates
                item["anpa_category"] = unique(category)
                item["subject"] = unique(item["subject"])

                # update event status SDCP-749
                if item.get("is_provisional", False):
                    eocstat_map = get_resource_service("vocabularies").find_one(
                        req=None, _id="eventoccurstatus"
                    )
                    item["occur_status"] = [
                        x
                        for x in eocstat_map.get("items", [])
                        if x["qcode"] == "eocstat:eos3" and x.get("is_active", True)
                    ][0]
                    item["occur_status"].pop("is_active", None)

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

    def find_event_type(self, event_types, qcode):
        for event_type in event_types:
            if (
                event_type.get("onclusive_ids")
                and str(qcode) in event_type["onclusive_ids"]
            ):
                return event_type

    def find_subject(self, subjects, name):
        for subject in subjects:
            if (
                subject.get("translations")
                and subject["translations"].get("name")
                and name.lower()
                in [
                    value.lower()
                    for value in subject["translations"]["name"].values()
                    if value
                ]
            ):
                return subject
            if subject["name"].lower() == name.lower():
                return subject
