# App Configuration Management Package

from .resource import AppConfigResource, AppConfigService


def init_app(app):
    """Initialize the app configuration app."""
    from superdesk import register_resource

    register_resource("app_config", AppConfigResource, AppConfigService, _app=app)


__all__ = ["AppConfigResource", "AppConfigService", "init_app"]
