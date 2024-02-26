from typing import NamedTuple

from .common import get_sort_date, set_item_metadata


class SortGroups(NamedTuple):
    """Geographic Regions used for grouping / sorting"""

    ATLANTIC: str
    QUEBEC: str
    OTTAWA: str
    ONTARIO: str
    PRAIRIES: str
    BRITISH_COLUMBIA: str
    NORTH: str
    UNDATED: str


SORT_GROUPS: SortGroups = SortGroups(
    "Atlantic",
    "Quebec",
    "Ottawa",
    "Ontario",
    "Prairies",
    "British Columbia",
    "North",
    "Undated",
)


STATE_GROUPS = {
    SORT_GROUPS.ATLANTIC: [
        "newfoundland and labrador",
        "nova scotia",
        "new brunswick",
        "prince edward island",
    ],
    SORT_GROUPS.QUEBEC: [
        "quebec",
    ],
    SORT_GROUPS.OTTAWA: [
        "ottawa",
    ],
    SORT_GROUPS.ONTARIO: [
        "ontario",
    ],
    SORT_GROUPS.PRAIRIES: [
        "manitoba",
        "saskatchewan",
        "alberta",
    ],
    SORT_GROUPS.BRITISH_COLUMBIA: [
        "british columbia",
    ],
    SORT_GROUPS.NORTH: [
        "nunavut",
        "northwest territories",
        "yukon",
    ],
}


def set_item_group(item):
    """Set the item's location to be used for grouping"""

    country = (item["address"].get("country") or "").lower()
    state = (item["address"].get("state") or "").lower()
    city = (item["address"].get("city") or "").lower()
    group = SORT_GROUPS.UNDATED

    if country == "canada":
        if state == SORT_GROUPS.ONTARIO.lower():
            group = SORT_GROUPS.OTTAWA if city == "ottawa" else SORT_GROUPS.ONTARIO
        else:
            for group_name, group_states in STATE_GROUPS.items():
                if state in group_states:
                    group = group_name
                    break

    item["group"] = group


def group_items_by_state(items):
    """Group the items by date / location

    Example Output format:
    {
        "2021-05-01": {
            "name": "Saturday, May 01",
            "groups": {
                "Atlantic": [{...}],
                "Quebec": [],
                "Ottawa": [{...}]
            }
        },
        "2021-05-02": {
            "name": "Sunday, May 02",
            "groups": {
                "Atlantic": [{...}],
                "Quebec": [],
                "Ottawa": [{...}]
            }
        }
    }
    """

    date_groups = {}

    # Iterate over the items, sorted by date. This way items are added
    # in the order they should be displayed in the output
    for item in sorted(items, key=lambda i: get_sort_date(i)):
        set_item_metadata(item)
        set_item_group(item)

        local_date_str = item["local_date_str"]
        if not date_groups.get(local_date_str):
            date_groups[local_date_str] = {
                # Format name for heading, i.e. Saturday, May 01
                "name": item["local_date"].strftime("%A, %B %d"),
                "groups": {
                    SORT_GROUPS.ATLANTIC: [],
                    SORT_GROUPS.QUEBEC: [],
                    SORT_GROUPS.OTTAWA: [],
                    SORT_GROUPS.ONTARIO: [],
                    SORT_GROUPS.PRAIRIES: [],
                    SORT_GROUPS.BRITISH_COLUMBIA: [],
                    SORT_GROUPS.NORTH: [],
                    SORT_GROUPS.UNDATED: [],
                },
            }

        date_groups[local_date_str]["groups"][item["group"]].append(item)

    return date_groups.items()
