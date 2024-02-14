import cp
import flask
import unittest
import superdesk

from unittest.mock import patch
from tests.mock import resources
from cp.macros.update_translation_metadata_macro import (
    update_translation_metadata_macro as macro,
)

import pytz
import settings
from superdesk import default_settings
from datetime import datetime, timedelta


class UpdateTranslationMetadataMacroTestCase(unittest.TestCase):
    def setUp(self):
        self.app = flask.Flask(__name__)

    def test_remove_destination_and_add_presse_canadienne_staff_as_destination(self):
        """
        Remove the current destination and add the Presse Canadienne staff as destination
        make the anpa_take_key as an empty string
        """

        item = {
            "_id": "urn:newsml:localhost:5000:2019-12-10T14:43:46.224107:d13ac5ae-7f43-4b7f-89a5-2c6835389564",
            "guid": "urn:newsml:localhost:5000:2019-12-10T14:43:46.224107:d13ac5ae-7f43-4b7f-89a5-2c6835389564",
            "headline": "test headline",
            "slugine": "test slugline",
            "state": "in_progress",
            "type": "text",
            "language": "en",
            "anpa_take_key": "update",
            "subject": [
                {"name": "Command News", "qcode": "CMPD1", "scheme": "destinations"}
            ],
        }

        with self.app.app_context():
            with patch.dict(superdesk.resources, resources):
                macro(item)

        self.assertIn("subject", item)
        self.assertIn(
            {
                "name": "Presse Canadienne staff",
                "qcode": "sfstf",
                "scheme": "destinations",
            },
            item["subject"],
        )
        self.assertEqual(item.get("anpa_take_key"), "")

    def test_override_destination_canadian_press_staff_to_presse_canadienne_staff(self):
        """
        If Canadian Press Staff destination is present override it with Presse Canadienne staff
        """
        item = {
            "_id": "urn:newsml:localhost:5000:2019-12-10T14:43:46.224107:d13ac5ae-7f43-4b7f-89a5-2c6835389564",
            "guid": "urn:newsml:localhost:5000:2019-12-10T14:43:46.224107:d13ac5ae-7f43-4b7f-89a5-2c6835389564",
            "headline": "test headline",
            "slugine": "test slugline",
            "state": "in_progress",
            "type": "text",
            "language": "en",
            "subject": [
                {
                    "name": "Canadian Press Staff",
                    "qcode": "cpstf",
                    "scheme": "destinations",
                }
            ],
        }

        with self.app.app_context():
            with patch.dict(superdesk.resources, resources):
                macro(item)

        self.assertIn("subject", item)
        self.assertIn(
            {
                "name": "Presse Canadienne staff",
                "qcode": "sfstf",
                "scheme": "destinations",
            },
            item["subject"],
        )

    def test_override_destination_the_associated_press_to_l_associated_press(self):
        """
        If The Associated Press destination is present override it with L'Associated Press
        """
        item = {
            "_id": "urn:newsml:localhost:5000:2019-12-10T14:43:46.224107:d13ac5ae-7f43-4b7f-89a5-2c6835389564",
            "guid": "urn:newsml:localhost:5000:2019-12-10T14:43:46.224107:d13ac5ae-7f43-4b7f-89a5-2c6835389564",
            "headline": "test headline",
            "slugine": "test slugline",
            "state": "in_progress",
            "type": "text",
            "language": "en",
            "subject": [
                {
                    "name": "The Associated Press",
                    "qcode": "ap---",
                    "scheme": "destinations",
                }
            ],
        }

        with self.app.app_context():
            with patch.dict(superdesk.resources, resources):
                macro(item)

        self.assertIn("subject", item)
        self.assertIn(
            {
                "name": "L'Associated Press",
                "qcode": "apfra",
                "scheme": "destinations",
            },
            item["subject"],
        )

    def test_destination_is_empty_add_presse_canadienne_staff(self):
        """
        If the destination is empty add Presse Canadienne staff
        """
        item = {
            "_id": "urn:newsml:localhost:5000:2019-12-10T14:43:46.224107:d13ac5ae-7f43-4b7f-89a5-2c6835389564",
            "guid": "urn:newsml:localhost:5000:2019-12-10T14:43:46.224107:d13ac5ae-7f43-4b7f-89a5-2c6835389564",
            "headline": "test headline",
            "slugine": "test slugline",
            "state": "in_progress",
            "type": "text",
            "keywords": ["foo", "bar"],
            "language": "en",
        }

        with self.app.app_context():
            with patch.dict(superdesk.resources, resources):
                macro(item)

        self.assertIn("subject", item)
        self.assertIn(
            {
                "name": "Presse Canadienne staff",
                "qcode": "sfstf",
                "scheme": "destinations",
            },
            item["subject"],
        )

    def test_dateline(self):
        self.app.config.update(
            {
                "GEONAMES_SEARCH_STYLE": settings.GEONAMES_SEARCH_STYLE,
                "GEONAMES_FEATURE_CLASSES": settings.GEONAMES_FEATURE_CLASSES,
                "GEONAMES_USERNAME": settings.GEONAMES_USERNAME,
                "GEONAMES_URL": default_settings.GEONAMES_URL,
                "GEONAMES_TOKEN": default_settings.GEONAMES_TOKEN,
            }
        )

        item = {
            "_id": "urn:newsml:localhost:5000:2019-12-10T14:43:46.224107:d13ac5ae-7f43-4b7f-89a5-2c6835389564",
            "guid": "urn:newsml:localhost:5000:2019-12-10T14:43:46.224107:d13ac5ae-7f43-4b7f-89a5-2c6835389564",
            "headline": "test headline",
            "slugine": "test slugline",
            "state": "in_progress",
            "type": "text",
            "dateline": {
                "date": datetime(2021, 7, 22, 00, 00, tzinfo=pytz.UTC),
                "text": "LONDON, Jun 22 testing source -",
                "source": "The Associated Press",
                "located": {
                    "alt_name": "",
                    "city": "London",
                    "city_code": "London",
                    "state": "England",
                    "state_code": "ENG",
                    "country": "United Kingdom",
                    "country_code": "GB",
                    "dateline": "city",
                    "location": {"lat": 51.50853, "lon": -0.12574},
                },
            },
        }

        with self.app.app_context():
            with patch.dict(superdesk.resources, resources):
                macro(item)

        dateline = item.get("dateline")
        self.assertEqual("The Associated Press", dateline["source"])
        self.assertIn("located", dateline)
        self.assertEqual("Londres", dateline["located"]["city"])
        self.assertEqual("Angleterre", dateline["located"]["state"])
        self.assertEqual("Royaume Uni", dateline["located"]["country"])
        self.assertEqual(51.50853, dateline["located"]["location"]["lat"])
        self.assertEqual(-0.12574, dateline["located"]["location"]["lon"])
