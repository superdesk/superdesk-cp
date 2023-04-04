from flask import current_app as app

from superdesk import get_resource_service
from superdesk.utc import utc_to_local


def get_sort_date(item):
    """Get date used for sorting of the output"""

    event_dates = (item.get("event") or {}).get("dates") or (item.get("dates") or {})
    return event_dates.get("start") or item["planning_date"]


def set_item_metadata(item):
    event = item.get("event") or {}
    set_item_title(item, event)
    set_item_description(item, event)
    set_item_dates(item, event)
    set_item_location(item, event)
    set_item_coverages(item)


def set_item_title(item, event):
    """Set the item's title

    Prioritise the Event's slugline/name before Planning item's
    """

    item["title"] = event.get("name") or item.get("name") or \
        event.get("slugline") or item.get("slugline") or \
        ""


def set_item_description(item, event):
    """Set the item's description

    Prioritise the Event's description before Planning item's
    """

    description = (
        event.get("definition_long") or
        item.get("definition_long") or
        event.get("definition_short") or
        item.get("definition_short") or
        item.get("description_text") or
        ""
    ).rstrip()
    short_description = (
        event.get("definition_short") or
        item.get("definition_short") or
        item.get("description_text") or
        ""
    ).rstrip()

    if description:
        if not description.endswith("."):
            description += ". "
        else:
            description += " "

    item["description"] = description
    item["description_short"] = short_description


def set_item_dates(item, event):
    """Set the item's dates to be used for sorting"""

    if item["type"] == "planning":
        # Use the Event dates if available
        # otherwise fall back to the Planning date
        if event.get("dates"):
            item["dates"] = item["event"]["dates"]
        else:
            item["dates"] = {
                "start": item["planning_date"],
                "tz": app.config["DEFAULT_TIMEZONE"]
            }

    # Construct the date string here so we don't have to use
    # {% if %} {% else %} statements in the template
    tz = item["dates"].get("tz") or app.config["DEFAULT_TIMEZONE"]
    start_local = utc_to_local(tz, item["dates"]["start"])
    start_local_str = start_local.strftime("%I:%M %P")
    end_local = utc_to_local(tz, item["dates"]["end"]) if item["dates"].get("end") else None
    end_local_str = end_local.strftime("%I:%M %P") if end_local else None
    tz_name = start_local.tzname()

    # If the `tz_name` doesn't include a timezone code,
    # then prefix with GMT
    if tz_name.startswith("+"):
        tz_name = f"GMT{tz_name}"

    item["local_date"] = start_local
    if end_local:
        item["local_time"] = f"{start_local_str} - {end_local_str} ({tz_name})"
    else:
        item["local_time"] = f"{start_local_str} ({tz_name})"

    # Set the date string used for grouping
    # in the format YYYY-MM-DD
    item["local_date_str"] = start_local.strftime("%Y-%m-%d")


def set_item_location(item, event):
    """Set the location to be used for sorting / displaying"""

    if item["type"] == "planning":
        item["location"] = event.get("location")

    item.setdefault("address", {})
    item["address"].setdefault("name", "")
    item["address"].setdefault("full", "")
    item["address"].setdefault("title", "")
    item["address"].setdefault("address", "")
    if len(item.get("location") or []):
        # Set the items Location details if available
        try:
            address_qcode = (item["location"][0] or {}).get("qcode")
            if address_qcode:
                address_item = get_resource_service("locations").find_one(req=None, guid=address_qcode) or {}
                address = address_item.get("address") or {}

                try:
                    address_line = (address.get("line") or [])[0]
                except IndexError:
                    address_line = ""

                item["address"] = {
                    "country": address["country"] if address.get("country") else None,
                    "locality": address["locality"] if address.get("locality") else None,
                    "city": address["city"] if address.get("city") else "",
                    "state": address["state"] if address.get("state") else None,
                    "name": address.get("city") or address_item.get("name") or "",
                    "full": address_item.get("unique_name") or address_item.get("formatted_address") or "",
                    "title": address_item.get("name") or "",
                    "address": address_line
                }
        except (IndexError, KeyError):
            pass

    # Set the name and full address to be used in the template
    if item["address"]["name"]:
        item["address"]["name"] = item["address"]["name"].upper()

    if item["address"]["title"] and item["address"]["address"]:
        item["address"]["short"] = item["address"]["title"] + ", " + item["address"]["address"]
    else:
        item["address"]["short"] = item["address"]["full"]

    if item["address"]["full"]:
        item["address"]["full"] = ". " + item["address"]["full"]


def set_item_coverages(item):
    """Set the item coverage information for the template to display"""

    item.setdefault("coverage_types", "")
    coverage_types = ", ".join(item.get("coverages") or [])
    if coverage_types:
        item["coverage_types"] = f"<br>Coverage: {coverage_types}"
