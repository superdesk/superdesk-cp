from flask import current_app as app
from typing import Union, Dict, Any
from datetime import datetime
import pytz
from eve.utils import str_to_date
import arrow

from superdesk import get_resource_service
from superdesk.utc import utc_to_local

MULTI_DAY_SECONDS = 24 * 60 * 60  # Number of seconds for an multi-day event
ALL_DAY_SECONDS = MULTI_DAY_SECONDS - 1  # Number of seconds for an all-day event


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
    item["formatted_time"] = get_event_formatted_dates(item)


def set_item_title(item, event):
    """Set the item's title

    Prioritise the Event's slugline/name before Planning item's
    """

    item["title"] = (
        event.get("name")
        or item.get("name")
        or event.get("slugline")
        or item.get("slugline")
        or ""
    )


def set_item_description(item, event):
    """Set the item's description

    Prioritise the Event's description before Planning item's
    """

    description = (
        event.get("definition_long")
        or item.get("definition_long")
        or event.get("definition_short")
        or item.get("definition_short")
        or item.get("description_text")
        or ""
    ).rstrip()
    short_description = (
        event.get("definition_short")
        or item.get("definition_short")
        or item.get("description_text")
        or ""
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
                "tz": app.config["DEFAULT_TIMEZONE"],
            }

    # Construct the date string here so we don't have to use
    # {% if %} {% else %} statements in the template
    tz = item["dates"].get("tz") or app.config["DEFAULT_TIMEZONE"]
    start_local = utc_to_local(tz, item["dates"]["start"])
    start_local_str = start_local.strftime("%I:%M %P")
    end_local = (
        utc_to_local(tz, item["dates"]["end"]) if item["dates"].get("end") else None
    )
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
                address_item = (
                    get_resource_service("locations").find_one(
                        req=None, guid=address_qcode
                    )
                    or {}
                )
                address = address_item.get("address") or {}

                try:
                    address_line = (address.get("line") or [])[0]
                except IndexError:
                    address_line = ""

                item["address"] = {
                    "country": address["country"] if address.get("country") else None,
                    "locality": (
                        address["locality"] if address.get("locality") else None
                    ),
                    "city": address["city"] if address.get("city") else "",
                    "state": address["state"] if address.get("state") else None,
                    "name": address.get("city") or address_item.get("name") or "",
                    "full": address_item.get("unique_name")
                    or address_item.get("formatted_address")
                    or "",
                    "title": address_item.get("name") or "",
                    "address": address_line,
                }
        except (IndexError, KeyError):
            pass

    # Set the name and full address to be used in the template
    if item["address"]["name"]:
        item["address"]["name"] = item["address"]["name"].upper()

    if item["address"]["title"] and item["address"]["address"]:
        item["address"]["short"] = (
            item["address"]["title"] + ", " + item["address"]["address"]
        )
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


def parse_date(datetime: Union[str, datetime]) -> datetime:
    """Return datetime instance for datetime."""
    if isinstance(datetime, str):
        try:
            return str_to_date(datetime)
        except ValueError:
            return arrow.get(datetime).datetime
    return datetime


def time_short(datetime: datetime, tz: pytz.BaseTzInfo):
    if datetime:
        return (
            parse_date(datetime)
            .astimezone(tz)
            .strftime(app.config.get("TIME_FORMAT_SHORT", "%H:%M"))
        )


def date_short(datetime: datetime, tz: pytz.BaseTzInfo):
    if datetime:
        return (
            parse_date(datetime)
            .astimezone(tz)
            .strftime(app.config.get("DATE_FORMAT_SHORT", "%d/%m/%Y"))
        )


def get_event_formatted_dates(event: Dict[str, Any]) -> str:
    start = event.get("dates", {}).get("start")
    end = event.get("dates", {}).get("end")
    all_day = event.get("dates", {}).get("all_day", False)
    tz_name: str = event.get("dates", {}).get("tz", app.config.get("DEFAULT_TIMEZONE"))
    tz = pytz.timezone(tz_name)

    duration_seconds = int((end - start).total_seconds())

    if all_day and duration_seconds == ALL_DAY_SECONDS:
        # All day event
        return "{}".format(date_short(start, tz))

    if duration_seconds >= MULTI_DAY_SECONDS:
        # Multi day event
        return "{} {} - {} {}".format(
            time_short(start, tz),
            date_short(start, tz),
            time_short(end, tz),
            date_short(end, tz),
        )

    if start == end:
        # start and end are the same

        if all_day:
            # all_day true
            return "{}".format(date_short(start, tz))
    
        return "{} {}".format(time_short(start, tz), date_short(start, tz))

    return "{} - {}, {}".format(
        time_short(start, tz), time_short(end, tz), date_short(start, tz)
    )
