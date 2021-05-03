from flask import current_app as app
from superdesk.utc import utc_to_local

STATE_GROUPS = {
    "Atlantic": [
        "newfoundland and labrador",
        "nova scotia",
        "new brunswick",
        "prince edward island",
    ],
    "Quebec": ["quebec"],
    "Ottawa": ["ottawa"],
    "Ontario": ["ontario"],
    "Prairies": ["manitoba", "saskatchewan", "alberta"],
    "British Columbia": ["british columbia"],
    "North": ["nunavut", "northwest territories", "yukon"],
    "Undated": [],
}


def set_item_details(items):
    for item in items:
        # Prioritise the Event's slugline/name before Planning item's
        item["title"] = item.get("slugline") or \
            item.get("name") or \
            ''

        # Prioritise the Event's description before Planning item's
        event = item.get("event") or item
        item["description"] = event.get("definition_long") or \
            event.get("definition_short") or \
            item.get("description_text") or \
            ''

        if item["type"] == "planning":
            # Use the Event dates if available
            # otherwise fall back to the Planning date
            if (item.get("event") or {}).get("dates"):
                item["dates"] = item["event"]["dates"]

                # Attach Events location/links for sorting/displaying
                item["location"] = item["event"].get("location")
                item["links"] = item["event"].get("links")
            else:
                item["dates"] = {
                    "start": item["planning_date"],
                    "tz": app.config["DEFAULT_TIMEZONE"]
                }

        item.setdefault("address", {})
        if len(item.get("location") or []):
            # Set the items Location details if available
            try:
                address = item["location"][0].get("address") or {}

                item["address"] = {
                    "country": address["country"] if address.get("country") else None,
                    "locality": address["locality"] if address.get("locality") else None,
                    "city": address["city"] if address.get("city") else None,
                    "state": address["state"] if address.get("state") else None,
                }
            except (IndexError, KeyError):
                pass

        # Construct the date string here so we don't have to use
        # {% if %} {% else %} statements in the template
        tz = item["dates"]["tz"]
        start_local = utc_to_local(tz, item["dates"]["start"])
        start_local_str = start_local.strftime('%I:%M %P')
        end_local = utc_to_local(tz, item["dates"]["end"]) if item["dates"].get("end") else None
        end_local_str = end_local.strftime('%I:%M %P') if end_local else None
        tz_name = start_local.tzname()

        if end_local:
            item["local_date"] = f'{start_local_str} - {end_local_str} ({tz_name})'
        else:
            item["local_date"] = f'{start_local_str} ({tz_name})'


def get_group_items(items, state_group):
    group_items = []

    for item in items:
        if item.get("_added_to_group"):
            # if this item has already been added to a group
            # then don't try and process it again
            continue

        add_to_group = False
        country = (item["address"].get("country") or "").lower()
        state = (item["address"].get("state") or "").lower()
        city = (item["address"].get("city") or "").lower()

        if country == "canada":
            if state == "ontario":
                if city == "ottawa" and state_group == "Ottawa":
                    add_to_group = True
                elif city != "ottawa" and state_group == "Ontario":
                    add_to_group = True
            elif state in STATE_GROUPS[state_group]:
                add_to_group = True
            elif state_group == "Undated":
                add_to_group = True
        elif state_group == "Undated":
            add_to_group = True

        if add_to_group:
            group_items.append(item)
            item["_added_to_group"] = True

    return sorted(group_items, key=lambda group_item: group_item["dates"]["start"])


def group_items_by_state(items):
    groups = {}

    set_item_details(items)
    for state_group in STATE_GROUPS:
        groups[state_group] = {
            "name": state_group,
            "_items": get_group_items(items, state_group),
        }

    return groups.items()
