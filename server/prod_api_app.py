import superdesk

from prod_api.app import get_app

from cp.usage_metrics import UsageResource, UsageService


application = get_app()

# fix pagination limit
application.config["PAGINATION_LIMIT"] = 200

superdesk.register_resource("usage_metrics", UsageResource, UsageService, _app=application)
