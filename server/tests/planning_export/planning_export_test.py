import unittest
import datetime
from flask import render_template
from app import get_app

events = [
    {
        "type": "event",
        "calendars": [{"is_active": True, "name": "Sport", "qcode": "sport"}],
        "language": "en",
        "name": "First",
        "dates": {
            "start": datetime.datetime(
                2024, 4, 22, 10, 30, 55, tzinfo=datetime.timezone.utc
            ),
            "end": datetime.datetime(
                2024, 4, 24, 15, 30, 59, tzinfo=datetime.timezone.utc
            ),
        },
    },
    {
        "type": "event",
        "calendars": [{"is_active": True, "name": "Sport", "qcode": "sport"}],
        "language": "en",
        "name": "second",
        "dates": {
            "start": datetime.datetime(
                2024, 7, 20, 8, 30, 00, tzinfo=datetime.timezone.utc
            ),
            "end": datetime.datetime(
                2024, 7, 20, 8, 30, 00, tzinfo=datetime.timezone.utc
            ),
            "all_day": True,
        },
    },
    {
        "type": "event",
        "calendars": [{"is_active": True, "name": "Sport", "qcode": "sport"}],
        "language": "en",
        "name": "third",
        "dates": {
            "start": datetime.datetime(
                2024, 7, 20, 00, 00, 00, tzinfo=datetime.timezone.utc
            ),
            "end": datetime.datetime(
                2024, 7, 20, 00, 00, 00, tzinfo=datetime.timezone.utc
            ),
        },
    },
    {
        "type": "event",
        "calendars": [{"is_active": True, "name": "Sport", "qcode": "sport"}],
        "language": "en",
        "name": "fourth",
        "dates": {
            "start": datetime.datetime(
                2024, 4, 22, 10, 30, 55, tzinfo=datetime.timezone.utc
            ),
            "end": datetime.datetime(
                2024, 4, 24, 15, 30, 59, tzinfo=datetime.timezone.utc
            ),
            "no_end_time": True,
        },
    },
    {
        "type": "event",
        "calendars": [{"is_active": True, "name": "Sport", "qcode": "sport"}],
        "language": "en",
        "name": "fifth",
        "dates": {
            "start": datetime.datetime(
                2024, 4, 22, 10, 30, 55, tzinfo=datetime.timezone.utc
            ),
            "end": datetime.datetime(
                2024, 4, 22, 15, 30, 59, tzinfo=datetime.timezone.utc
            ),
            "no_end_time": True,
        },
    },
]


class ParserTestCase(unittest.TestCase):

    app = get_app()

    def test_new_one(self):
        with self.app.app_context():
            template_data = render_template(
                "news_events_list_export.html", items=events, app=self.app
            )
        self.assertIn(
            "<p>First<br> _ 06:30 AM 2024-04-22 - 11:30 AM 2024-04-24</p>",
            template_data,
        )
        self.assertIn(
            "<p>third<br> _ 08:00 PM 2024-07-19</p>",
            template_data,
        )
        self.assertIn(
            "<p>second<br> _ 2024-07-20</p>",
            template_data,
        )
        self.assertIn(
            "<p>fourth<br> _ 06:30 AM 2024-04-22 - 2024-04-24</p>",
            template_data,
        )
        self.assertIn(
            "<p>fifth<br> _ 06:30 AM 2024-04-22</p>",
            template_data,
        )
