from babel.dates import format_date

from superdesk import get_resource_service

from .common import get_sort_date, set_item_metadata


SORT_GROUPS = [
    "Général",
    "Affaires",
    "Culture"
]


def get_french_name(item) -> str:
    return ((item.get("translations") or {}).get("name") or {}).get("fr-CA") or item.get("name")


def set_item_group(item, item_translations):
    """Set the item's topic from Calendar or Agenda for grouping"""

    names = []
    if len(item.get("calendars") or []):
        names = [
            item_translations["calendars"].get(calendar.get("qcode"))
            for calendar in item["calendars"]
        ]
    elif len(item.get("agendas") or []):
        # Agendas are converted from `_id` to Agenda item in `planning_article_export` endpoint
        names = [
            item_translations["agendas"].get(agenda.get("_id"))
            for agenda in item["agendas"]
        ]

    if not len(names):
        return

    for group in SORT_GROUPS:
        if group.lower() in names:
            item["group"] = group
            return


def set_item_coverage_names(item, item_translations):
    """Convert the item's `coverages` to list of coverage types (in French)

    The `planning_article_export` endpoint converts the `coverages`
    attribute into a list of strings, i.e.
    [
        'Text'
        'Text (cancelled)'
        'Photo (cancelled)'
    ]

    So we have to rsplit by ' ' to get the name of the coverage type
    To remove '(cancelled)' from the coverage entry
    """

    coverage_names = [
        item_translations["coverage_types"].get(coverage_type.rsplit(" ", 1)[0])
        for coverage_type in item.get("coverages") or []
    ]

    coverage_types = ", ".join(coverage_names)
    if coverage_types:
        item["coverage_types"] = f"<br>Couverture: {coverage_types}"


def group_items_by_french_topics(items):
    """Group the items by date / calendar/agenda

    Example Output format:
    {
        "2021-05-01": {
            "name": "Saturday, May 01",
            "groups": {
                "Général": [{...}],
                "Affaires": [],
                "Culture": [{...}]
            }
        },
        "2021-05-02": {
            "name": "Sunday, May 02",
            "groups": {
                "Général": [{...}],
                "Affaires": [],
                "Culture": [{...}]
            }
        }
    }
    """

    date_groups = {}

    # Generate map of French translations here
    # So we don't have to do this for every item
    vocabs_service = get_resource_service("vocabularies")
    item_translations = {
        "calendars": {
            calendar.get("qcode"): get_french_name(calendar).lower()
            for calendar in vocabs_service.find_one(req=None, _id="event_calendars").get("items") or []
        },
        "agendas": {
            agenda.get("_id"): get_french_name(agenda).lower()
            for agenda in get_resource_service("agenda").find(where={})
        },
        "coverage_types": {
            coverage_type.get("name"): get_french_name(coverage_type)
            for coverage_type in vocabs_service.find_one(req=None, _id="g2_content_type").get("items") or []
        },
    }

    # Iterate over the items, sorted by date. This way items are added
    # in the order they should be displayed in the output
    for item in sorted(items, key=lambda i: get_sort_date(i)):
        set_item_metadata(item)
        set_item_group(item, item_translations)
        set_item_coverage_names(item, item_translations)

        # Skip this item if a group was not found
        # otherwise we may end up with empty date entries in the export
        if not item.get("group"):
            continue

        local_date_str = item["local_date_str"]
        if not date_groups.get(local_date_str):
            date_groups[local_date_str] = {
                # Format name for heading, in Canadian French i.e.
                # jeudi, juin 24
                "name": format_date(item["local_date"], "EEEE, MMM d", locale="fr_CA"),
                "groups": {
                    group: []
                    for group in SORT_GROUPS
                },
            }

        date_groups[local_date_str]["groups"][item["group"]].append(item)

    return date_groups.items()
