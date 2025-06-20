import superdesk
from superdesk.eve_async.service import AsyncBaseService
from superdesk.auth_server.scopes import Scope

from prod_api.items.resource import item_url


async def get_users(items):
    user_ids = [item["user"] for item in items]
    return {
        _id: await superdesk.get_resource_service("users").find_one_async(
            req=None, _id=_id
        )
        for _id in user_ids
    }


class UsageResource(superdesk.Resource):
    url = f"items/<{item_url}:item>/usage"
    resource_title = "item_usage"
    resource_methods = ["GET"]
    privileges = {"GET": Scope.ARCHIVE_READ.name}
    datasource = {
        "source": "usage_metrics",
        "projection": dict(
            user=1,
            date=1,
            action=1,
            _etag=0,
            _created=0,
            _updated=0,
        ),
    }


class UsageService(AsyncBaseService):
    async def on_fetched_async(self, doc):
        await super().on_fetched_async(doc)

        users = await get_users(doc["_items"])

        for item in doc["_items"]:
            user_id = item.pop("user")
            user = users.get(user_id)
            item["user"] = user["email"]

            # clean up
            item.pop("_id")
            item.pop("_etag")
            item.pop("_links")
            item.pop("_created")
            item.pop("_updated")
