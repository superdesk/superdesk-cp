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
            }
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
    ]

class ParserTestCase(unittest.TestCase):

    app = get_app()

    def test_new_one(self):
        with self.app.app_context():
            template_data = render_template(
                "news_events_list_export.html", items=events, app=self.app
            )
        self.assertIn(
                "<p>First<br> _ 06:30 22/04/2024 - 11:30 24/04/2024</p>",
                template_data,
            )
        self.assertIn(
                "<p>third<br> _ 20:00 19/07/2024</p>",
                template_data,
            )
        self.assertIn(
                "<p>second<br> _ 20/07/2024</p>",
                template_data,
            )