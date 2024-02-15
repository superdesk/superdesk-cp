from .news_event_list import group_items_by_state
from .french_news_events_list import group_items_by_french_topics


def init_app(app):
    app.jinja_env.globals.update(group_items_by_state=group_items_by_state)
    app.jinja_env.globals.update(
        group_items_by_french_topics=group_items_by_french_topics
    )
