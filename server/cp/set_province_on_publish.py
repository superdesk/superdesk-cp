from superdesk import get_resource_service
from superdesk.signals import item_publish_async

PROVINCE_CV = "regions"


async def set_province_on_publish(item, updates):
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
    provinces = await get_resource_service("vocabularies").get_items_async(
        PROVINCE_CV, is_active=True
    )
    for province in provinces:
        if province.get("name", "").lower() == region.lower():
            updates["subject"].append(province)
            item["subject"] = updates["subject"]
            return


def init_app(app):
    item_publish_async.connect(set_province_on_publish)
