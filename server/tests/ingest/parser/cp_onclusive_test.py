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


def qcode(subject):
    return "{}:{}".format(subject.get("scheme"), subject.get("qcode"))


class OnclusiveFeedParserTestCase(ParserTestCase):
    parser = CPOnclusiveFeedParser()
    provider = "Test_CP_Onclusive"
    app = flask.Flask(__name__)

    maxDiff = None

    def test_content(self):
        with self.app.app_context():
            with patch.dict(superdesk.resources, resources):
                item = self.parser.parse(data)[0]
                expected_subjects = [
                    {
                        "name": "Conflict / Terrorism / Security",
                        "qcode": "133",
                        "scheme": "onclusive_categories",
                    },
                    {
                        "name": "UK Regional Elections",
                        "qcode": "148",
                        "scheme": "onclusive_event_types",
                    },
                    {
                        "name": "Testing",
                        "qcode": "149",
                        "scheme": "onclusive_event_types",
                    },
                    {
                        "name": "Banking",
                        "qcode": "159",
                        "scheme": "onclusive_categories",
                    },
                    {
                        "name": "Music Festivals",
                        "qcode": "228",
                        "scheme": "onclusive_event_types",
                    },
                    {
                        "name": "Testing2",
                        "qcode": "129",
                        "scheme": "onclusive_event_types",
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
                        "name": "Law & Order",
                        "qcode": "88",
                        "scheme": "onclusive_categories",
                    },
                    {
                        "name": "Trade Conferences",
                        "qcode": "97",
                        "scheme": "onclusive_categories",
                    },
                    {
                        "qcode": "Conference",
                        "scheme": "event_types",
                    },
                    {
                        "qcode": "Conference and trade show",
                        "scheme": "event_types",
                    },
                    {
                        "qcode": "Official visit",
                        "scheme": "event_types",
                    },
                    {
                        "qcode": "00000035",
                        "scheme": "subject_custom",
                    },
                    {
                        "qcode": "00000050",
                        "scheme": "subject_custom",
                    },
                    {
                        "qcode": "00000097",
                        "scheme": "subject_custom",
                    },
                    {
                        "qcode": "00000133",
                        "scheme": "subject_custom",
                    },
                    {
                        "qcode": "00000159",
                        "scheme": "subject_custom",
                    },
                    {
                        "qcode": "02000000",  # mapped via cp_index
                        "scheme": "subject_custom",
                    },
                ]
                self.assertEqual(
                    sorted(map(qcode, item["subject"])),
                    sorted(map(qcode, expected_subjects)),
                )
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
                self.assertEqual(item[ITEM_TYPE], CONTENT_TYPE.EVENT)
                self.assertEqual(item["state"], CONTENT_STATE.INGESTED)

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

                self.assertEqual(
                    item["name"],
                    "Annual Forum on Anti-Money Laundering and Financial Crime",
                )
                self.assertEqual(item["definition_short"], "")

                self.assertEqual(
                    item["location"][0]["name"],
                    "One King West Hotel & Residence, 1 King St W, Toronto",
                )

                self.assertEqual(item["is_provisional"], False)
                self.assertEqual(item["occur_status"]["qcode"], "eocstat:eos5")

                data[0]["isProvisional"] = True
                item = self.parser.parse(data)[0]
                self.assertEqual(item["is_provisional"], True)
                self.assertEqual(item["occur_status"]["qcode"], "eocstat:eos3")
