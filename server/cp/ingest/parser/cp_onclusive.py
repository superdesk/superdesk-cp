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
        items = super().parse(content, provider)

        for item in items:
            category = []
            if item.get("subject"):
                for subject in item.get("subject"):
                    onclusive_category = self.is_exist(
                        onclusive_cv_items, subject["qcode"]
                    )
                    if onclusive_category:
                        anpa_category = self.is_exist(
                            anpa_categories, onclusive_category["cp_category"]
                        )
                        if anpa_category:
                            category.append(anpa_category)

            item["anpa_category"] = category
            self.event.append(item)
        return self.event

    def is_exist(self, cv_items, qcode):
        """
        Check the item is exist in the cv.
        """
        for item in cv_items:
            if item["qcode"] == qcode:
                return item
