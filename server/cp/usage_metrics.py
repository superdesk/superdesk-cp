import superdesk

from prod_api.items.resource import item_url
from superdesk.auth_server.scopes import Scope


def get_users(items):
    user_ids = [item["user"] for item in items]
    return {
        _id: superdesk.get_resource_service("users").find_one(req=None, _id=_id)
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


class UsageService(superdesk.Service):
    def on_fetched(self, doc):
        super().on_fetched(doc)

        users = get_users(doc["_items"])

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
