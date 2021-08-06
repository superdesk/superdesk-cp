from flask_babel import _
from babel.dates import format_date

from superdesk import get_resource_service
from superdesk.errors import SuperdeskApiError

from .common import get_sort_date, set_item_metadata

GROUP_QCODE_ORDER = [
    "fr-surveiller",  # À surveiller
    "fr-general",  # Général
    "fr-politique-can",  # Politique fédérale
    "fr-politique-qc",  # Politique québécoise
    "fr-actualites",  # Actualités
    "fr-relations-travail",  # Relations de travail
    "fr-affaires",  # Affaires
    "fr-justice-faits-divers",  # Justice et faits divers
    "fr-environnement",  # Environnement
    "fr-societe",  # Société
    "fr-science-sante",  # Science et santé
    "fr-tendances",  # Tendances
    "fr-techno",  # Technologies
    "fr-sports",  # Sports
    "fr-culture",  # Culture
    "fr-atlantique",  # Atlantique
    "fr-ailleurs-canada",  # Ailleurs au Canada
    "fr-international",  # International
]


def get_french_name(item) -> str:
    return ((item.get("translations") or {}).get("name") or {}).get("fr-CA") or item.get("name")


def set_item_group(item):
    """Set the item's topic from Calendar or Agenda for grouping"""

    qcodes = []
    if len(item.get("calendars") or []):
        qcodes = [
            calendar.get("qcode")
            for calendar in item["calendars"]
        ]
    elif len(item.get("agendas") or []):
        # Agendas are converted from `_id` to Agenda item in `planning_article_export` endpoint
        qcodes = [
            agenda.get("_id")
            for agenda in item["agendas"]
        ]

    if not len(qcodes):
        return

    for qcode in GROUP_QCODE_ORDER:
        if qcode in qcodes:
            item["group"] = qcode
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

    item["coverage_types"] = ", ".join(coverage_names)


def group_items_by_french_topics(items):
    """Group the items by date / calendar/agenda

    Example Output format:
    {
        "2021-05-01": {
            "name": "jeudi, juin 24",
            "groups": {
                "À surveiller": [{...}],
                "Général": [],
                "Politique fédérale": [{...}]
            }
        },
        "2021-05-02": {
            "name": "jeudi, juin 25",
            "groups": {
                "À surveiller": [{...}],
                "Général": [],
                "Politique fédérale": [{...}]
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
            calendar.get("qcode"): get_french_name(calendar).upper()
            for calendar in vocabs_service.find_one(req=None, _id="event_calendars").get("items") or []
        },
        "coverage_types": {
            coverage_type.get("name"): get_french_name(coverage_type).lower()
            for coverage_type in vocabs_service.find_one(req=None, _id="g2_content_type").get("items") or []
        },
    }

    # Iterate over the items, sorted by date. This way items are added
    # in the order they should be displayed in the output
    for item in sorted(items, key=lambda i: get_sort_date(i)):
        set_item_metadata(item)
        set_item_group(item)
        set_item_coverage_names(item, item_translations)

        if item["description_short"] and not item["description_short"].endswith("."):
            item["description_short"] += "."

        # Skip this item if a group was not found
        # otherwise we may end up with empty date entries in the export
        if not item.get("group"):
            continue

        local_date_str = item["local_date_str"]
        if not date_groups.get(local_date_str):
            date_groups[local_date_str] = {
                # Format name for heading, in Canadian French i.e.
                # jeudi 24 juin
                "name": format_date(item["local_date"], "EEEE d MMM", locale="fr_CA").capitalize(),
                "groups": {
                    item_translations["calendars"].get(qcode): []
                    for qcode in GROUP_QCODE_ORDER
                },
            }

        group_name = item_translations["calendars"].get(item["group"])
        date_groups[local_date_str]["groups"][group_name].append(item)

    if not date_groups:
        raise SuperdeskApiError.badRequestError(_("No items matched the required calendar/agenda"))

    return date_groups.items()
