from superdesk.signals import item_publish


def set_byline_on_publish(sender, item, updates, **kwargs):
    updated = item.copy()
    updated.update(updates)

    if updated.get("byline") or not updated.get("authors"):
        return

    byline = ", ".join([author["name"] for author in item.get("authors", [])])

    item["byline"] = updates["byline"] = byline


def init_app(app):
    item_publish.connect(set_byline_on_publish)
