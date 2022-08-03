import json
from cp.ingest.parser.cp_onclusive import CPOnclusiveFeedParser
import datetime
from dateutil.tz import tzutc
from . import ParserTestCase
from superdesk.metadata.item import (
    ITEM_TYPE,
    CONTENT_TYPE,
    GUID_FIELD,
    CONTENT_STATE,
)
import flask
import superdesk
from tests.ingest.parser import get_fixture_path
from tests.mock import resources
from unittest.mock import patch


with open(get_fixture_path("cp_onclusive.json", "cp_onclusive")) as fp:
    data = json.load(fp)


class OnclusiveFeedParserTestCase(ParserTestCase):
    parser = CPOnclusiveFeedParser()
    provider = "Test_CP_Onclusive"
    app = flask.Flask(__name__)

    def test_content(self):
        with self.app.app_context():
            with patch.dict(superdesk.resources, resources):
                item = self.parser.parse(data)[0]
                item["subject"].sort(key=lambda i: i["name"])
                expected_subjects = [
                    {
                        "name": "Law & Order",
                        "qcode": "88",
                        "scheme": "onclusive_categories",
                    },
                    {
                        "name": "Conflict / Terrorism / Security",
                        "qcode": "133",
                        "scheme": "onclusive_categories",
                    },
                    {
                        "name": "Trade Conferences",
                        "qcode": "97",
                        "scheme": "onclusive_categories",
                    },
                    {
                        "name": "Banking",
                        "qcode": "159",
                        "scheme": "onclusive_categories",
                    },
                    {
                        "name": "Finance General",
                        "qcode": "35",
                        "scheme": "onclusive_categories",
                    },
                    {
                        "name": "Tech - Internet, software & new media",
                        "qcode": "50",
                        "scheme": "onclusive_categories",
                    },
                    {
                        "name": "Trade Conferences",
                        "qcode": "148",
                        "scheme": "onclusive_event_types",
                    },
                    {
                        "name": "Cyber Security and Fraud",
                        "qcode": "228",
                        "scheme": "onclusive_event_types",
                    },
                ]
                expected_subjects.sort(key=lambda i: i["name"])
                self.assertEqual(item["subject"], expected_subjects)
                item["anpa_category"].sort(key=lambda i: i["name"])
                expected_categories = [
                    {
                        "name": "National",
                        "qcode": "g",
                        "translations": {
                            "name": {
                                "en-CA": "National",
                                "fr-CA": "Nouvelles Générales",
                            }
                        },
                    },
                    {
                        "name": "International",
                        "qcode": "w",
                        "translations": {
                            "name": {"en-CA": "International", "fr-CA": "International"}
                        },
                    },
                    {
                        "name": "Business",
                        "qcode": "b",
                        "translations": {
                            "name": {"en-CA": "Business", "fr-CA": "Affaires"}
                        },
                    },
                ]
                expected_categories.sort(key=lambda i: i["name"])
                self.assertEqual(item["anpa_category"], expected_categories)
                self.assertEqual(
                    item["event_types"],
                    [
                        {
                            "event_name": "Cyber Security and Fraud",
                            "defination": "Events or issues relating to cyber security and fraud",
                        },
                        {
                            "event_name": "Trade Conferences",
                            "defination": (
                                "Responsible business and corporate citizenship"
                                " covering ethical, social, environmental, and sustainability issues."
                                " Business sustainability tries to minimise any negative economic,"
                                " environmental and social impact, or potentially have a positive impact"
                                ", on a local or global level"
                            ),
                        },
                    ],
                )
                self.assertEqual(
                    item[GUID_FIELD], "urn:newsml:2021-05-04T21:19:10.2:4112034"
                )
                self.assertEqual(item[ITEM_TYPE], CONTENT_TYPE.EVENT)
                self.assertEqual(item["state"], CONTENT_STATE.INGESTED)
                self.assertEqual(
                    item["firstcreated"],
                    datetime.datetime(2021, 5, 4, 21, 19, 10, 200000, tzinfo=tzutc()),
                )
                self.assertEqual(
                    item["versioncreated"],
                    datetime.datetime(2022, 5, 10, 13, 14, 34, 873000, tzinfo=tzutc()),
                )

                self.assertEqual(item["occur_status"]["qcode"], "eocstat:eos5")

                self.assertIn(
                    "https://www.canadianinstitute.com/anti-money-laundering-financial-crime/",
                    item["links"],
                )

                self.assertEqual(
                    item["dates"]["start"],
                    datetime.datetime(2022, 6, 15, 0, 0, tzinfo=tzutc()),
                )
                self.assertEqual(
                    item["dates"]["end"],
                    datetime.datetime(2022, 6, 16, 0, 0, tzinfo=tzutc()),
                )
                self.assertEqual(item["dates"]["tz"], "EDT")

                self.assertEqual(
                    item["name"],
                    "Annual Forum on Anti-Money Laundering and Financial Crime",
                )
                self.assertEqual(item["definition_short"], "")

                self.assertEqual(
                    item["location"][0]["name"],
                    "One King West Hotel & Residence, 1 King St W, Toronto",
                )
