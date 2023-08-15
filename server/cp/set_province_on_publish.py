import superdesk

from superdesk.signals import item_publish

PROVINCE_CV = "regions"


def set_province_on_publish(sender, item, updates, **kwargs):
    try:
        region = item["dateline"]["located"]["state"]
    except (AttributeError, KeyError, TypeError):
        return
    if not region:
        return
    updates.setdefault("subject", item.get("subject") or [])
    for subj in updates["subject"]:
        if subj.get("scheme") == PROVINCE_CV:
            return
    provinces = superdesk.get_resource_service("vocabularies").get_items(
        PROVINCE_CV, is_active=True
    )
    for province in provinces:
        if province.get("name", "").lower() == region.lower():
            updates["subject"].append(province)
            item["subject"] = updates["subject"]
            return


def init_app(app):
    item_publish.connect(set_province_on_publish)
