import superdesk

from prod_api.app import get_app

from cp.usage_metrics import UsageResource, UsageService


application = get_app(dict(
    PRODAPI_AUTH_ENABLED=False,
))

superdesk.register_resource("usage_metrics", UsageResource, UsageService, _app=application)
