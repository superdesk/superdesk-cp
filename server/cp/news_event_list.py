from superdesk.utc import utc_to_local

STATE_GROUPS = {
    "atlantic": [
        "newfoundland and labrador",
        "nova scotia",
        "new brunswick",
        "prince edward island",
    ],
    "quebec": ["quebec"],
    "ottawa": ["ottawa"],
    "ontario": ["ontario"],
    "prairies": ["manitoba", "saskatchewan", "alberta"],
    "british columbia": ["british columbia"],
    "north": ["nunavut", "northwest territories", "yukon"],
    "miscellaneous": [],
}


def get_group_items(items, state_group):
    group_items = []

    for item in items:
        tz = item['dates']['tz']
        item['dates']['start_local'] = utc_to_local(tz, item['dates']['start'])
        item['dates']['end_local'] = utc_to_local(tz, item['dates']['end'])
        item['dates']['tz_name'] = item['dates']['end_local'].tzname()

        if item.get("location"):
            try:
                country = item["location"][0]["address"]["country"].lower()
                locality = item["location"][0]["address"]["locality"].lower()

                if country != "canada" and state_group == "miscellaneous":
                    group_items.append(item)
                elif country == "canada" and locality in STATE_GROUPS[state_group]:
                    group_items.append(item)
                elif state_group == "miscellaneous":
                    group_items.append(item)
            except (IndexError, KeyError):
                if state_group == "miscellaneous":
                    group_items.append(item)
        elif state_group == "miscellaneous":
            group_items.append(item)

    return sorted(group_items, key=lambda group_item: group_item["dates"]["start"])


def group_items_by_state(items):
    groups = {}

    for state_group in STATE_GROUPS:
        groups[state_group] = {
            "name": state_group,
            "_items": get_group_items(items, state_group),
        }

    return groups
