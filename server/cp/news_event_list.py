STATE_GROUPS = {
    'atlantic': ['newfoundland and labrador', 'nova scotia', 'new brunswick', 'prince edward island'],
    'quebec': ['quebec'],
    'ottawa': ['ottawa'],
    'ontario': ['ontario'],
    'prairies': ['manitoba', 'saskatchewan', 'alberta'],
    'british columbia': ['british columbia'],
    'north': ['nunavut', 'northwest territories', 'yukon'],
    'miscellaneous': []
}

def get_group_items(items, state_group):
    group_items = []

    for item in items:
        if item.get('location'):
            country = item['location'][0]['address']['country'].lower()
            locality = item['location'][0]['address']['locality'].lower()

            if country != 'canada' and state_group == 'miscellaneous':
                group_items.append(item)
            elif country == 'canada' and locality in STATE_GROUPS[state_group]:
                group_items.append(item)
    return sorted(group_items, key=lambda group_item: group_item['dates']['start'])


def group_items_by_state(items):
    groups = {}

    for state_group in STATE_GROUPS:
        groups[state_group] = {
            'name': state_group,
            '_items': get_group_items(items, state_group)
        }

    return groups
