import datetime
from superdesk.tests import TestCase
from superdesk.flask import render_template


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


class ParserTestCase(TestCase):
    app_config = {"DEFAULT_TIMEZONE": "America/Toronto"}

    async def test_new_one(self):
        template_data = await render_template(
            "news_events_list_export.html", items=events, app=self.app
        )
        self.assertIn(
            "<p>First<br>06:30 AM 2024-04-22 - 11:30 AM 2024-04-24<br></p>",
            template_data,
        )
        self.assertIn(
            "<p>third<br>08:00 PM 2024-07-19<br></p>",
            template_data,
        )
        self.assertIn(
            "<p>second<br>2024-07-20<br></p>",
            template_data,
        )
        self.assertIn(
            "<p>fourth<br>06:30 AM 2024-04-22 - 2024-04-24<br></p>",
            template_data,
        )
        self.assertIn(
            "<p>fifth<br>06:30 AM 2024-04-22<br></p>",
            template_data,
        )

    async def test_embedded_location_fallback(self):
        template_data = await render_template(
            "news_events_list_export.html",
            items=[
                {
                    "type": "event",
                    "calendars": [
                        {"is_active": True, "name": "Sport", "qcode": "sport"}
                    ],
                    "language": "en",
                    "name": "Embedded location event",
                    "dates": {
                        "start": datetime.datetime(
                            2024, 9, 13, 13, 0, 0, tzinfo=datetime.timezone.utc
                        ),
                        "end": datetime.datetime(
                            2024, 9, 13, 13, 0, 0, tzinfo=datetime.timezone.utc
                        ),
                    },
                    "location": [
                        {
                            "name": "Ada X, 4001 Rue Berri, Montreal, QC",
                            "qcode": "onclusive-venue:383014",
                            "address": {
                                "country": "Canada",
                                "state": "Quebec",
                            },
                            "formatted_address": "Quebec Canada",
                        }
                    ],
                }
            ],
            app=self.app,
        )
        self.assertIn("09:00 AM 2024-09-13 Ada X, 4001 Rue Berri, Montreal, QC", template_data)
        self.assertNotIn(". Quebec Canada", template_data)
